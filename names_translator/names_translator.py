from __future__ import annotations

import re
import csv

from functools import cache
from importlib import resources
from typing import Callable, Iterable, Optional

from translitua import (
    translit,
    ALL_RUSSIAN,
    ALL_UKRAINIAN,
    UkrainianKMU,
    RussianInternationalPassport,
)

from ._text import is_cyr, is_ukr, normalize_key, replace_apostrophes, title
from .dicts import NameDicts, default_dicts

__all__ = [
    "is_cyr",
    "is_ukr",
    "title",
    "replace_apostrophes",
    "normalize_key",
    "Transliterator",
]


@cache
def _load_legacy_translations() -> dict[str, list[str]]:
    # Process-wide, like the compiled dictionaries: parsed at most once
    translations = {}

    with resources.files("names_translator").joinpath("data/ua2ru.csv").open(
        "r", encoding="utf8"
    ) as fp:
        for l in csv.DictReader(fp):
            translations[normalize_key(l["term"])] = list(
                filter(None, [l["translation"], l["alt_translation"]])
            )

    return translations


class Transliterator:
    special_cases = {
        "Юлія": ["Julia", "Yulia"],
        "Юлия": ["Julia", "Yulia"],
        "Дмитро": ["Dmitry", "Dimitry"],
        "Дмитрий": ["Dmitry", "Dimitry"],
        "Євген": ["Eugene"],
        "Петро": ["Peter"],
        "Ірина": ["Irene"],
        "Юрій": ["Youriy"],
    }

    special_replacements = {
        r"ий$": ["y", "i", "yy"],
        r"ий\s": ["y ", "i ", "yy "],
        r"кс": ["x"],
    }

    def __init__(self, dicts: Optional[NameDicts] = None) -> None:
        # Dictionaries are loaded on first lookup, not on construction,
        # so that importing/instantiating stays cheap
        self._ru_translations: Optional[dict[str, list[str]]] = None
        self._dicts = dicts if dicts is not None else default_dicts()

    @property
    def ru_translations(self) -> dict[str, list[str]]:
        if self._ru_translations is None:
            self._ru_translations = _load_legacy_translations()
        return self._ru_translations

    def get_name(self, name_tuple: Iterable[str]) -> str:
        return " ".join(name_tuple).strip().replace("  ", " ")

    def replace_item(
        self, name_tuple: Iterable[str], chunk: str, repl: str
    ) -> list[str]:
        chunk_lower = chunk.lower()
        return [repl if x.lower() == chunk_lower else x for x in name_tuple]

    def _translate_chunk(self, chunk: str, category: str) -> list[str]:
        if not is_cyr(chunk):
            return [chunk]

        key = normalize_key(chunk)

        # Compiled per-category dictionaries (when installed) win over the
        # legacy ua2ru.csv, which stays as a coverage-preserving fallback
        if self._dicts.available:
            translations = self._dicts.lookup_key(key, category)
            if translations:
                return translations

        return self.ru_translations.get(key, [chunk])

    def _add_transliterations(
        self,
        name_tuples: Iterable[tuple[str, str, str]],
        accept: Callable[[str], bool],
        tables: Iterable,
        heuristic_table,
        use_heuristic_replacements: bool,
        result: set[str],
    ) -> None:
        for n in name_tuples:
            name = self.get_name(n)

            if not accept(name):
                continue

            for table in tables:
                result.add(translit(name, table))

            if not use_heuristic_replacements:
                continue

            for sc_rex, replacements in self.special_replacements.items():
                if re.search(sc_rex, name, flags=re.I | re.U):
                    for repl in replacements:
                        optional_n = re.sub(sc_rex, repl, name, flags=re.I | re.U)
                        result.add(translit(title(optional_n), heuristic_table))

            for sc, replacements in self.special_cases.items():
                if sc in n:
                    for repl in replacements:
                        optional_n = self.replace_item(n, sc, repl)
                        result.add(translit(self.get_name(optional_n), heuristic_table))

    def transliterate(
        self,
        person_last_name: str,
        person_first_name: str,
        person_patronymic: str,
        include_original_name: bool = True,
        translate_into_russian: bool = True,
        use_russian_transliteration: bool = True,
        use_ukrainian_transliteration: bool = True,
        use_heuristic_replacements: bool = True,
    ) -> set[str]:

        original = [
            (person_last_name, person_first_name, person_patronymic)
        ]

        result = set()
        if include_original_name:
            for orig in original:
                result.add(self.get_name(orig))

        if translate_into_russian:
            translated = [
                (l, f, p)

                for f in self._translate_chunk(person_first_name, "first")
                for p in self._translate_chunk(person_patronymic, "patronymic")
                for l in self._translate_chunk(person_last_name, "last")
            ]
            result.update(map(self.get_name, translated))
        else:
            translated = original

        if use_ukrainian_transliteration:
            self._add_transliterations(
                original,
                is_cyr,
                ALL_UKRAINIAN,
                UkrainianKMU,
                use_heuristic_replacements,
                result,
            )

        if use_russian_transliteration:
            self._add_transliterations(
                translated,
                lambda name: not is_ukr(name),
                ALL_RUSSIAN,
                RussianInternationalPassport,
                use_heuristic_replacements,
                result,
            )

        return result
