from __future__ import annotations

import json
import os
from functools import cache, cached_property
from typing import Optional

from ._text import normalize_key, title

__all__ = ["CATEGORIES", "FORMAT_VERSION", "NameDicts", "default_dicts"]

# Also the lookup order when no category is given: a bare name is more
# likely a first name or patronymic than one of ~120k last names
CATEGORIES = ("first", "patronymic", "last")

# Storage format, shared with the compiler (names_translator.dict_compiler):
# <category>.dawg is a RecordDAWG(">BH") keyed by the normalized ukrainian
# name with (rank, rule_id) records — rank 0 is the most frequent variant,
# and the DAWG returns a key's records sorted, so lookups come back
# pre-ranked; <category>.rules.json is the rule table indexed by rule id.
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
    """Compiled per-category uk->ru dictionaries (RecordDAWG + rule table).

    The files are produced by the names_translator.dict_compiler module and
    shipped in the optional names-translator-dicts-uk package. Everything is
    loaded lazily on first lookup. When no dictionaries can be found, every
    lookup returns [].

    Dictionary location, first match wins:
    1. explicit ``path`` constructor argument
    2. the ``NAMES_TRANSLATOR_DICTS_PATH`` environment variable
    3. the installed ``names_translator_dicts_uk`` package
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = path
        self._loaded: dict = {}

    @cached_property
    def _base(self) -> Optional[str]:
        path = self._path or os.environ.get("NAMES_TRANSLATOR_DICTS_PATH")
        if not path:
            try:
                import names_translator_dicts_uk

                path = names_translator_dicts_uk.get_path()
            except ImportError:
                return None

        if not os.path.isdir(path):
            return None

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

    def _get(self, category: str):
        if category not in CATEGORIES:
            raise ValueError(
                "unknown category %r, expected one of %s" % (category, CATEGORIES)
            )

        if category not in self._loaded:
            self._loaded[category] = self._load(category)

        return self._loaded[category]

    def _load(self, category: str):
        if self._base is None:
            return None

        dawg_path = os.path.join(self._base, category + ".dawg")
        rules_path = os.path.join(self._base, category + ".rules.json")
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
        for cat in (category,) if category else CATEGORIES:
            loaded = self._get(cat)
            if loaded is None:
                continue

            d, rules = loaded
            records = d.get(key)
            if records is None:
                continue

            for _, rule_id in records:  # sorted by the leading rank
                translation = apply_rule(key, rules[rule_id])
                if translation not in results:
                    results.append(translation)

        return results[:limit]


@cache
def default_dicts() -> NameDicts:
    """Process-wide shared instance, so DAWGs are loaded at most once."""
    return NameDicts()
