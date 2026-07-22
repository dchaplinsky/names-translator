import json
import os.path
import shutil

from importlib import resources

import pytest

from names_translator import Transliterator
from names_translator.dicts import NameDicts


def _load_golden(name):
    with open(
        os.path.join(os.path.dirname(__file__), name), encoding="utf8"
    ) as fp:
        return set(json.load(fp))


@pytest.fixture(scope="session")
def legacy_dir(tmp_path_factory):
    # A data dir with only the legacy pool: reproduces the pre-2.0
    # dictionary behavior of ua2ru.csv
    tmp = tmp_path_factory.mktemp("legacy-dicts")
    data = resources.files("names_translator") / "data"
    for name in ("legacy.dawg", "legacy.rules.json"):
        shutil.copy(str(data / name), tmp)
    return str(tmp)


@pytest.fixture(scope="session")
def tr_legacy(legacy_dir):
    # Legacy-mode instance, pinned by the pre-2.0 golden fixture
    return Transliterator(dicts=NameDicts(path=legacy_dir))


@pytest.fixture(scope="session")
def tr():
    # The out-of-the-box behavior: full bundled dictionaries
    return Transliterator()


@pytest.fixture(scope="session")
def golden():
    return _load_golden("golden_chaplinsky.json")


@pytest.fixture(scope="session")
def golden_default():
    return _load_golden("golden_chaplinsky_dicts.json")
