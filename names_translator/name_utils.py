import re
from string import capwords

from names_translator import Transliterator
from translitua import translit, UkrainianKMU

TRANSLITERATOR = Transliterator()


def title(s):
    chunks = s.split()
    chunks = map(lambda x: capwords(x, "-"), chunks)
    return " ".join(chunks)


def parse_fullname(person_name):
    # Extra care for initials (especialy those without space)
    person_name = re.sub(r"\s+", " ",
                         person_name.replace(".", ". ").replace('\xa0', " "))

    chunks = person_name.strip().split(" ")

    last_name = ""
    first_name = ""
    patronymic = ""
    dob = ""

    numeric_chunks = list(
        filter(lambda x: re.search(r"\d+\.?", x), chunks)
    )

    chunks = list(
        filter(lambda x: re.search(r"\d+\.?", x) is None, chunks)
    )

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
    return {
        title(name),
        translit(title(name), UkrainianKMU)
    }

def concat_name(*args):
    return " ".join(filter(None, args))
