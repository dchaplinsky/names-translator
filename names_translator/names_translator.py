import re
import os.path
import csv

from string import capwords

def is_cyr(name):
    return re.search("[а-яіїєґ]+", name.lower(), re.UNICODE) is not None


def is_ukr(name):
    return re.search("['іїєґ]+", name.lower(), re.UNICODE) is not None


def title(s):
    chunks = s.split()
    chunks = map(lambda x: capwords(x, u"-"), chunks)
    return u" ".join(chunks)


def replace_apostrophes(s):
    return s.replace("`", "'").replace("’", "'")


class Transliterator(object):
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
        "ий$": ["y", "i", "yy"],
        "ий\s": ["y ", "i ", "yy "],
        "кс": ["x"],
    }

    def get_name(self, name_tuple):
        return " ".join(name_tuple).strip().replace("  ", " ")

    def replace_item(self, name_tuple, chunk, repl):
        r = [repl if x.lower() == chunk.lower() else x for x in name_tuple]
        return r

    def __init__(self, *args, **kwargs):
        self.ru_translations = {}

        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "data/ua2ru.csv"), "r") as fp:
            r = csv.DictReader(fp)
            for l in r:
                self.ru_translations[l["term"].lower()] = list(
                    filter(None, [l["translation"], l["alt_translation"]]))

        return super(Transliterator, self).__init__(*args, **kwargs)

    def transliterate(self,
                      person_last_name,
                      person_first_name,
                      person_patronymic,
                      include_original_name=True,
                      translate_into_russian=True,
                      use_russian_transliteration=True,
                      use_ukrainian_transliteration=True,
                      use_heuristic_replacements=True):

        from translitua import (
            translit, ALL_RUSSIAN, ALL_UKRAINIAN, UkrainianKMU, RussianInternationalPassport)


        first_names = []
        last_names = []
        patronymics = []

        original = [
            (person_last_name, person_first_name, person_patronymic)
        ]

        result = set()
        if include_original_name:
            for orig in original:
                result.add(self.get_name(orig))

        if translate_into_russian:
            if (person_first_name.lower() in self.ru_translations and
                    is_cyr(person_first_name)):
                first_names = self.ru_translations[person_first_name.lower()]
            else:
                first_names = [person_first_name]

            if (person_last_name.lower() in self.ru_translations and
                    is_cyr(person_last_name)):
                last_names = self.ru_translations[person_last_name.lower()]
            else:
                last_names = [person_last_name]

            if (person_patronymic.lower() in self.ru_translations and
                    is_cyr(person_patronymic)):
                patronymics = self.ru_translations[person_patronymic.lower()]
            else:
                patronymics = [person_patronymic]

        translated = [
            (l, f, p)

            for f in first_names
            for p in patronymics
            for l in last_names
        ]

        if use_ukrainian_transliteration:
            for n in original:
                name = self.get_name(n)

                if is_cyr(name):
                    for ua_table in ALL_UKRAINIAN:
                        result.add(translit(name, ua_table))

                    if use_heuristic_replacements:
                        for sc_rex, replacements in self.special_replacements.items():
                            if re.search(sc_rex, name, flags=re.I | re.U):
                                for repl in replacements:
                                    optional_n = re.sub(sc_rex, repl, name, flags=re.I | re.U)
                                    result.add(translit(title(optional_n), UkrainianKMU))

                        for sc, replacements in self.special_cases.items():
                            if sc in n:
                                for repl in replacements:
                                    optional_n = self.replace_item(n, sc, repl)
                                    result.add(translit(self.get_name(optional_n), UkrainianKMU))

        if use_russian_transliteration:
            for n in translated:
                name = self.get_name(n)

                if not is_ukr(name):
                    for ru_table in ALL_RUSSIAN:
                        result.add(translit(name, ru_table))

                    if use_heuristic_replacements:
                        for sc_rex, replacements in self.special_replacements.items():
                            if re.search(sc_rex, name, flags=re.I | re.U):
                                for repl in replacements:
                                    optional_n = re.sub(sc_rex, repl, name, flags=re.I | re.U)
                                    result.add(translit(title(optional_n), RussianInternationalPassport))

                        for sc, replacements in self.special_cases.items():
                            if sc in n:
                                for repl in replacements:
                                    optional_n = self.replace_item(n, sc, repl)
                                    result.add(translit(self.get_name(optional_n), RussianInternationalPassport))

        return result | set(map(self.get_name, translated))
