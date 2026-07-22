from __future__ import annotations

import json
import os
from functools import cache, cached_property
from importlib import resources
from typing import Optional

from ._text import normalize_key, title

__all__ = [
    "CATEGORIES",
    "FORMAT_VERSION",
    "LEGACY",
    "POOLS",
    "NameDicts",
    "default_dicts",
]

# Also the lookup order when no category is given: a bare name is more
# likely a first name or patronymic than one of ~120k last names
CATEGORIES = ("first", "patronymic", "last")

# General pool compiled from the historical ua2ru dictionary (no category
# information); consulted only when the category dictionaries have no match
LEGACY = "legacy"

POOLS = CATEGORIES + (LEGACY,)

# Storage format, shared with the compiler (names_translator.dict_compiler):
# <pool>.dawg is a RecordDAWG(">BH") keyed by the normalized ukrainian
# name with (rank, rule_id) records — rank 0 is the most frequent variant,
# and the DAWG returns a key's records sorted, so lookups come back
# pre-ranked; <pool>.rules.json is the rule table indexed by rule id.
# Bump on any incompatible layout change.
FORMAT_VERSION = 1
RECORD_FORMAT = ">BH"

# Limits implied by the record layout above
MAX_RANK = 255
MAX_RULES = 1 << 16


def make_rule(key: str, translation: str) -> tuple[int, str, bool]:
    """Encode a translation as a diff against its normalized key.

    Diffing keeps the DAWG payload alphabet tiny and shared, which is what
    lets it compress ~5x better than storing full translations.
    """
    lower = translation.lower()
    prefix_len = len(os.path.commonprefix([key, lower]))
    rule = (len(key) - prefix_len, lower[prefix_len:], True)

    if apply_rule(key, rule) != translation:
        # Not reconstructible via title-casing — store verbatim
        rule = (len(key), translation, False)

    return rule


def apply_rule(key: str, rule: tuple[int, str, bool]) -> str:
    drop, suffix, titlecase = rule
    result = key[: len(key) - drop] + suffix
    if not titlecase:
        return result
    if " " in result or "-" in result:
        return title(result)
    # Fast path: for a single lowercase token capitalize() == title()
    return result.capitalize()


class NameDicts:
    """Compiled uk->ru dictionaries (RecordDAWG + rule tables).

    Three per-category pools (first/patronymic/last) plus a general legacy
    pool used as a fallback. The files are produced by the
    names_translator.dict_compiler module and bundled with the package.
    Everything is loaded lazily on first lookup; a pool that cannot be
    found simply yields no results.

    Dictionary location, first match wins:
    1. explicit ``path`` constructor argument
    2. the ``NAMES_TRANSLATOR_DICTS_PATH`` environment variable
    3. the data bundled with the package
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = path
        self._loaded: dict = {}
        self._as_dicts: dict = {}

    @cached_property
    def _base(self) -> Optional[str]:
        path = self._path or os.environ.get("NAMES_TRANSLATOR_DICTS_PATH")
        if path:
            # A user-supplied location may legitimately be absent
            if not os.path.isdir(path):
                return None
        else:
            path = str(resources.files("names_translator") / "data")
            missing = [
                name
                for pool in POOLS
                for name in ("%s.dawg" % pool, "%s.rules.json" % pool)
                if not os.path.exists(os.path.join(path, name))
            ]
            if missing:
                # Unlike the above, missing bundled data is always a broken
                # installation — fail loudly, not with identity translations
                raise RuntimeError(
                    "bundled dictionaries at %s are missing %s — broken or "
                    "unsupported (zipped?) installation"
                    % (path, ", ".join(missing))
                )

        manifest_path = os.path.join(path, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf8") as fp:
                version = json.load(fp).get("format_version", FORMAT_VERSION)
            if version > FORMAT_VERSION:
                raise RuntimeError(
                    "dictionaries at %s use format_version %d, but this "
                    "names_translator only supports up to %d — upgrade the "
                    "names_translator package" % (path, version, FORMAT_VERSION)
                )

        return path

    @property
    def available(self) -> bool:
        return self._base is not None

    def _get(self, pool: str):
        if pool not in POOLS:
            raise ValueError(
                "unknown pool %r, expected one of %s" % (pool, POOLS)
            )

        if pool not in self._loaded:
            self._loaded[pool] = self._load(pool)

        return self._loaded[pool]

    def _load(self, pool: str):
        if self._base is None:
            return None

        dawg_path = os.path.join(self._base, pool + ".dawg")
        rules_path = os.path.join(self._base, pool + ".rules.json")
        if not (os.path.exists(dawg_path) and os.path.exists(rules_path)):
            return None

        # Lazy import: tools/bench_dict_vs_dawg.py relies on stubbing
        # sys.modules["dawg"] before this point to force the pure reader
        try:
            from dawg import RecordDAWG  # C extension reader (the "fast" extra)
        except ImportError:
            from dawg_python import RecordDAWG

        d = RecordDAWG(RECORD_FORMAT)
        d.load(dawg_path)

        with open(rules_path, encoding="utf8") as fp:
            rules = json.load(fp)

        return d, rules

    def _collect(self, key: str, pool: str, results: list[str]) -> None:
        loaded = self._get(pool)
        if loaded is None:
            return

        d, rules = loaded
        records = d.get(key)
        if records is None:
            return

        for _, rule_id in records:  # sorted by the leading rank
            translation = apply_rule(key, rules[rule_id])
            if translation not in results:
                results.append(translation)

    def lookup(
        self,
        name: str,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[str]:
        """Ranked russian translations of a ukrainian name chunk."""
        return self.lookup_key(normalize_key(name), category, limit)

    def lookup_key(
        self,
        key: str,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[str]:
        """Same as lookup(), for a key that is already normalize_key-ed."""
        results: list[str] = []
        for pool in (category,) if category else CATEGORIES:
            self._collect(key, pool, results)

        if not results:
            self._collect(key, LEGACY, results)

        return results[:limit]

    def as_dict(self, pool: str) -> dict[str, list[str]]:
        """The whole pool as {normalized name: ranked translations}."""
        if pool not in self._as_dicts:
            result: dict[str, list[str]] = {}
            loaded = self._get(pool)
            if loaded is not None:
                d, rules = loaded
                for key, (_, rule_id) in d.iteritems():  # per key, rank order
                    result.setdefault(key, []).append(
                        apply_rule(key, rules[rule_id])
                    )
            self._as_dicts[pool] = result

        return self._as_dicts[pool]


@cache
def default_dicts() -> NameDicts:
    """Process-wide shared instance, so DAWGs are loaded at most once."""
    return NameDicts()
