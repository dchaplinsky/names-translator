import subprocess
import sys

from names_translator.name_utils import (
    concat_name,
    generate_all_names,
    parse_and_generate,
    parse_fullname,
    try_to_fix_mixed_charset,
)


def test_parse_fullname_three_chunks():
    assert parse_fullname("Чаплинський Дмитро Олександрович") == (
        "Чаплинський",
        "Дмитро",
        "Олександрович",
        "",
    )


def test_parse_fullname_two_chunks():
    assert parse_fullname("Чаплинський Дмитро") == ("Чаплинський", "Дмитро", "", "")


def test_parse_fullname_single_chunk():
    assert parse_fullname("Сковорода") == ("Сковорода", "", "", "")


def test_parse_fullname_empty():
    assert parse_fullname("") == ("", "", "", "")


def test_parse_fullname_initials_without_spaces():
    assert parse_fullname("Іванов І.І.") == ("Іванов", "І.", "І.", "")


def test_parse_fullname_nbsp():
    assert parse_fullname("Іванов\xa0Іван") == ("Іванов", "Іван", "", "")


def test_parse_fullname_dob():
    assert parse_fullname("Чаплинський Дмитро Олександрович 01.01.1980") == (
        "Чаплинський",
        "Дмитро",
        "Олександрович",
        "01.01.1980",
    )


def test_parse_fullname_long_last_name():
    assert parse_fullname("Нечуй Левицький Іван Семенович") == (
        "Нечуй Левицький",
        "Іван",
        "Семенович",
        "",
    )


def test_try_to_fix_mixed_charset_to_cyr():
    # Іванoв with a latin "o" is fixable into pure cyrillic
    mixed = "Іванoв"
    fixed = try_to_fix_mixed_charset(mixed)
    assert fixed == "Іванов"
    assert "o" not in fixed


def test_try_to_fix_mixed_charset_unfixable():
    # "д" has no latin counterpart and "d" has no cyrillic one
    assert try_to_fix_mixed_charset("Дмитроd") == "Дмитроd"


def test_try_to_fix_mixed_charset_pure_names_untouched():
    assert try_to_fix_mixed_charset("Іванов") == "Іванов"
    assert try_to_fix_mixed_charset("Ivanov") == "Ivanov"


def test_concat_name():
    assert concat_name("Іван", "", "Петрович") == "Іван Петрович"
    assert concat_name() == ""


def test_generate_all_names_with_position():
    res = generate_all_names("Чаплинський", "Дмитро", "Олександрович", "CEO")
    assert res
    assert all(name.endswith(", CEO") for name in res)


def test_parse_and_generate():
    res = parse_and_generate("Чаплинський Дмитро Олександрович")
    assert "Chaplynskyi Dmytro Oleksandrovych" in res


def test_import_does_not_load_dictionary():
    """Importing name_utils must not load any DAWG; the first lookup does."""
    code = (
        "import names_translator.name_utils as nu; "
        "assert not nu.TRANSLITERATOR._dicts._loaded; "
        "nu.TRANSLITERATOR.transliterate('Чаплинський', 'Дмитро', ''); "
        "assert nu.TRANSLITERATOR._dicts._loaded"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
