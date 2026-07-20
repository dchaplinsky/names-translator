"""Text helpers shared by the transliterator and the dictionary layer.

A leaf module: must not import anything from this package, so that both
names_translator.py and dicts.py can depend on it without cycles.
"""

from __future__ import annotations

import re
import unicodedata

from string import capwords

# Apostrophe flavours real-world data mixes with the plain '
_APOSTROPHES = "`’ʼ´"

_CYR_RE = re.compile(r"[а-яёіїєґ]+")
_UKR_RE = re.compile(r"['%sіїєґ]+" % _APOSTROPHES)

_APOSTROPHES_TRANS = str.maketrans(dict.fromkeys(_APOSTROPHES, "'"))


def is_cyr(name: str) -> bool:
    return _CYR_RE.search(name.lower()) is not None


def is_ukr(name: str) -> bool:
    return _UKR_RE.search(name.lower()) is not None


def title(s: str) -> str:
    return " ".join(capwords(chunk, "-") for chunk in s.split())


def replace_apostrophes(s: str) -> str:
    return s.translate(_APOSTROPHES_TRANS)


def normalize_key(s: str) -> str:
    # Dictionary keys and lookups must agree on unicode form, case and
    # apostrophe flavour
    return replace_apostrophes(unicodedata.normalize("NFC", s)).lower()
