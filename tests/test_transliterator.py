import os.path

import pytest

from names_translator import is_cyr, is_ukr, normalize_key


def test_golden_chaplinsky(tr, golden):
    """Default behavior is locked to the output captured before the 2.0 refactoring."""
    assert tr.transliterate("Чаплинський", "Дмитро", "Олександрович") == golden


def test_readme_example_matches_golden(golden):
    """The usage example in README.rst must not drift from the golden fixture."""
    readme = os.path.join(os.path.dirname(__file__), os.pardir, "README.rst")

    names = set()
    with open(readme, encoding="utf8") as fp:
        for line in fp:
            line = line.strip()
            if line.startswith(("{", "'", '"')) and line.endswith((",", "}")):
                item = line.lstrip("{").rstrip(",}").strip()
                if len(item) > 1 and item[0] == item[-1] and item[0] in "'\"":
                    names.add(item[1:-1])

    assert names == golden


def test_include_original_name(tr):
    res = tr.transliterate("Чаплинський", "Дмитро", "Олександрович")
    assert "Чаплинський Дмитро Олександрович" in res
    assert "Чаплинский Дмитрий Александрович" in res


@pytest.mark.parametrize("apostrophe", ["'", "’", "ʼ", "`"])
def test_apostrophe_variants_hit_dictionary(tr, apostrophe):
    """All apostrophe flavours must find the same ua2ru dictionary entry."""
    res = tr.transliterate("П{}ятчанін".format(apostrophe), "Дмитро", "")
    assert any("Пьятчанин" in x for x in res)


def test_russian_transliteration_without_translation(tr):
    """translate_into_russian=False must not disable Russian transliteration."""
    res = tr.transliterate(
        "Чаплинский",
        "Дмитрий",
        "Александрович",
        include_original_name=False,
        translate_into_russian=False,
        use_ukrainian_transliteration=False,
        use_russian_transliteration=True,
    )
    assert "Chaplinskiy Dmitriy Aleksandrovich" in res
    assert "Чаплинский Дмитрий Александрович" not in res


def test_all_flags_off_is_empty(tr):
    res = tr.transliterate(
        "Чаплинський",
        "Дмитро",
        "Олександрович",
        include_original_name=False,
        translate_into_russian=False,
        use_ukrainian_transliteration=False,
        use_russian_transliteration=False,
    )
    assert res == set()


def test_missing_patronymic(tr):
    res = tr.transliterate("Чаплинський", "Дмитро", "")
    assert "Чаплинський Дмитро" in res
    assert not any("  " in name for name in res)


def test_is_cyr():
    assert is_cyr("Дмитро")
    assert is_cyr("Пётр")
    assert is_cyr("Подъячев")
    assert not is_cyr("Smith")


def test_is_ukr():
    assert is_ukr("Олексій")
    assert is_ukr("Мар'яна")
    assert is_ukr("Мар’яна")
    assert not is_ukr("Дмитрий")


def test_normalize_key():
    assert normalize_key("П’ятчанін") == normalize_key("П'ятчанін")
    assert normalize_key("Пʼятчанін") == normalize_key("п'ятчанін")
    # NFC: composed й vs decomposed и + ̆ combining breve
    assert normalize_key("Юрій") == normalize_key("\u042e\u0440\u0456\u0438\u0306")
