import re
from string import capwords
from operator import itemgetter

from names_translator import Transliterator
from translitua import translit, UkrainianKMU

TRANSLITERATOR = Transliterator()


def title(s):
    chunks = s.split()
    chunks = map(lambda x: capwords(x, "-"), chunks)
    return " ".join(chunks)


def is_cyr(name):
    return re.search("[а-яіїєґ]+", name.lower(), re.UNICODE) is not None


def is_ukr(name):
    return re.search("['іїєґ]+", name.lower(), re.UNICODE) is not None


def is_eng(name):
    return re.search("[a-z]+", name.lower(), re.UNICODE) is not None


def is_greek(name):
    return re.search("[α-ωίϊΐόάέύϋΰήώ]+", name.lower(), re.UNICODE) is not None


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


def try_to_fix_mixed_charset(name):
    if is_cyr(name) and is_eng(name):
        name_cyr = name.translate(E2C_TRANS)

        if not is_eng(name_cyr):
            return name_cyr

        name_eng = name.translate(C2E_TRANS)
        if not is_cyr(name_eng):
            return name_eng

    return name


def parse_fullname(person_name):
    # Extra care for initials (especialy those without space)
    person_name = re.sub(
        r"\s+", " ", person_name.replace(".", ". ").replace("\xa0", " ")
    )

    chunks = person_name.strip().split(" ")

    last_name = ""
    first_name = ""
    patronymic = ""
    dob = ""

    numeric_chunks = list(filter(lambda x: re.search(r"\d+\.?", x), chunks))

    chunks = list(filter(lambda x: re.search(r"\d+\.?", x) is None, chunks))

    if len(chunks) == 2:
        last_name = title(chunks[0])
        first_name = title(chunks[1])
    elif len(chunks) > 2:
        last_name = title(" ".join(chunks[:-2]))
        first_name = title(chunks[-2])
        patronymic = title(chunks[-1])

    if numeric_chunks:
        dob = "".join(numeric_chunks)

    return last_name, first_name, patronymic, dob


def generate_all_names(l, f, p, position=None):
    res = set()
    for tr_name in TRANSLITERATOR.transliterate(l, f, p):
        if position is None:
            res.add(title(tr_name))
        else:
            res.add("{}, {}".format(title(tr_name), position))

    return res


def parse_and_generate(name, position=None):
    l, f, p, _ = parse_fullname(name)
    return generate_all_names(l, f, p, position)


def autocomplete_suggestions(name):
    return {title(name), translit(title(name), UkrainianKMU)}


def concat_name(*args):
    return " ".join(filter(None, args))
