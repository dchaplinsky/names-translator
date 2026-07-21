import csv
import json

import pytest

from names_translator import Transliterator, dict_compiler
from names_translator.dicts import NameDicts, apply_rule, make_rule

FIXTURES = {
    "first": [
        ("Олександр", "Александр", 100),
        ("Олександр", "Олександр", 7),
        ("Юлія", "Юлия", 50),
    ],
    "last": [
        ("Пʼятниця", "Пятница", 15),
    ],
}


@pytest.fixture(scope="module")
def compiled_dir(tmp_path_factory):
    pytest.importorskip("dawg")  # the C-extension builder
    tmp = tmp_path_factory.mktemp("dicts")

    categories = {}
    for category, rows in FIXTURES.items():
        source = tmp / "{}.csv".format(category)
        with open(source, "w", encoding="utf8", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(["uk", "ru", "count"])
            writer.writerows(rows)
        categories[category] = [str(source)]

    dict_compiler.compile_dicts(categories, str(tmp))
    return str(tmp)


@pytest.fixture(scope="module")
def dicts(compiled_dir):
    return NameDicts(path=compiled_dir)


@pytest.fixture(scope="module")
def tr_dicts(dicts):
    return Transliterator(dicts=dicts)


@pytest.mark.parametrize(
    "key,value",
    [
        ("чорний", "Черный"),
        ("п'ятниця", "Пятница"),
        ("абв", "Где"),
        ("нечуй-левицький", "Нечуй-Левицкий"),
        ("макдональд", "МакДональд"),  # not title-caseable -> verbatim rule
    ],
)
def test_rule_roundtrip(key, value):
    assert apply_rule(key, make_rule(key, value)) == value


def test_lookup_ranked_by_count(dicts):
    assert dicts.available
    assert dicts.lookup("Олександр", "first") == ["Александр", "Олександр"]


def test_lookup_normalizes_case_and_apostrophes(dicts):
    assert dicts.lookup("ОЛЕКСАНДР", "first")[0] == "Александр"
    for apostrophe in ["'", "’", "ʼ", "`"]:
        assert dicts.lookup("П{}ятниця".format(apostrophe), "last") == ["Пятница"]


def test_lookup_limit_and_missing(dicts):
    assert dicts.lookup("Олександр", "first", limit=1) == ["Александр"]
    assert dicts.lookup("Небувалий", "first") == []


def test_lookup_all_categories(dicts):
    # No category hint: all compiled categories are consulted, and the
    # "patronymic" one is silently absent from the fixture
    assert dicts.lookup("Юлія") == ["Юлия"]
    assert dicts.lookup("Пʼятниця") == ["Пятница"]


def test_lookup_unknown_category(dicts):
    with pytest.raises(ValueError):
        dicts.lookup("Юлія", "middle")


def test_unavailable_dicts(tmp_path):
    dicts = NameDicts(path=str(tmp_path / "missing"))
    assert not dicts.available
    assert dicts.lookup("Олександр", "first") == []


def test_env_var_discovery(compiled_dir, monkeypatch):
    monkeypatch.setenv("NAMES_TRANSLATOR_DICTS_PATH", compiled_dir)
    assert NameDicts().available


def test_future_format_version_rejected(tmp_path):
    with open(tmp_path / "manifest.json", "w", encoding="utf8") as fp:
        json.dump({"format_version": 999}, fp)

    with pytest.raises(RuntimeError, match="format_version 999"):
        NameDicts(path=str(tmp_path)).available


def test_transliterator_uses_compiled_dicts(tr_dicts):
    res = tr_dicts.transliterate("Пʼятниця", "Олександр", "")

    assert "Пятница Александр" in res
    assert "Пятница Олександр" in res


def test_transliterator_falls_back_to_legacy_csv(tr_dicts):
    # П'ятчанін is not in the compiled fixture but is in the bundled ua2ru.csv
    res = tr_dicts.transliterate("П'ятчанін", "Олександр", "")

    assert any("Пьятчанин Александр" in name for name in res)
