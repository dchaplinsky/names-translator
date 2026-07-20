from __future__ import annotations

import re
from operator import itemgetter
from typing import Optional

from translitua import translit, UkrainianKMU

from .names_translator import Transliterator, is_cyr, is_ukr, title

__all__ = [
    "title",
    "is_cyr",
    "is_ukr",
    "is_eng",
    "is_greek",
    "try_to_fix_mixed_charset",
    "parse_fullname",
    "generate_all_names",
    "parse_and_generate",
    "autocomplete_suggestions",
    "concat_name",
    "TRANSLITERATOR",
]

# Cheap to construct: the dictionary itself is loaded lazily on first lookup
TRANSLITERATOR = Transliterator()

_ENG_RE = re.compile(r"[a-z]+")
_GREEK_RE = re.compile(r"[α-ωίϊΐόάέύϋΰήώ]+")
_NUMERIC_RE = re.compile(r"\d+\.?")


def is_eng(name: str) -> bool:
    return _ENG_RE.search(name.lower()) is not None


def is_greek(name: str) -> bool:
    return _GREEK_RE.search(name.lower()) is not None


C2E = (
    ("а", "a"),
    ("в", "b"),
    ("е", "e"),
    ("и", "u"),
    ("і", "i"),
    ("к", "k"),
    ("м", "m"),
    ("н", "h"),
    ("о", "o"),
    ("п", "n"),
    ("р", "p"),
    ("с", "c"),
    ("у", "y"),
    ("х", "x"),
)

C2E += tuple((k.upper(), v.upper()) for k, v in C2E)

E2C = tuple((v, k) for k, v in C2E)

C2E_TRANS = str.maketrans(
    "".join(map(itemgetter(0), C2E)), "".join(map(itemgetter(1), C2E))
)
E2C_TRANS = str.maketrans(
    "".join(map(itemgetter(0), E2C)), "".join(map(itemgetter(1), E2C))
)


def try_to_fix_mixed_charset(name: str) -> str:
    if is_cyr(name) and is_eng(name):
        name_cyr = name.translate(E2C_TRANS)

        if not is_eng(name_cyr):
            return name_cyr

        name_eng = name.translate(C2E_TRANS)
        if not is_cyr(name_eng):
            return name_eng

    return name


def parse_fullname(person_name: str) -> tuple[str, str, str, str]:
    # Extra care for initials (especially those without space)
    person_name = re.sub(
        r"\s+", " ", person_name.replace(".", ". ").replace("\xa0", " ")
    )

    last_name = ""
    first_name = ""
    patronymic = ""
    dob = ""

    chunks = []
    numeric_chunks = []
    for chunk in person_name.strip().split(" "):
        if _NUMERIC_RE.search(chunk):
            numeric_chunks.append(chunk)
        else:
            chunks.append(chunk)

    if len(chunks) == 1:
        last_name = title(chunks[0])
    elif len(chunks) == 2:
        last_name = title(chunks[0])
        first_name = title(chunks[1])
    elif len(chunks) > 2:
        last_name = title(" ".join(chunks[:-2]))
        first_name = title(chunks[-2])
        patronymic = title(chunks[-1])

    if numeric_chunks:
        dob = "".join(numeric_chunks)

    return last_name, first_name, patronymic, dob


def generate_all_names(
    l: str, f: str, p: str, position: Optional[str] = None
) -> set[str]:
    res = set()
    for tr_name in TRANSLITERATOR.transliterate(l, f, p):
        if position is None:
            res.add(title(tr_name))
        else:
            res.add("{}, {}".format(title(tr_name), position))

    return res


def parse_and_generate(name: str, position: Optional[str] = None) -> set[str]:
    l, f, p, _ = parse_fullname(name)
    return generate_all_names(l, f, p, position)


def autocomplete_suggestions(name: str) -> set[str]:
    return {title(name), translit(title(name), UkrainianKMU)}


def concat_name(*args: str) -> str:
    return " ".join(filter(None, args))
