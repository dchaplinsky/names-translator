import json
import os.path

import pytest

from names_translator import Transliterator, name_utils
from names_translator.dicts import NameDicts


@pytest.fixture(scope="session", autouse=True)
def _force_legacy_dicts():
    # Golden behavior must not depend on whether the optional dicts package
    # happens to be installed on the machine running the tests
    name_utils.TRANSLITERATOR = Transliterator(
        dicts=NameDicts(path=os.path.join(os.path.dirname(__file__), "no-such-dir"))
    )


@pytest.fixture(scope="session")
def tr(_force_legacy_dicts):
    # The same instance the library helpers use, so the dictionary
    # is loaded once per test run
    return name_utils.TRANSLITERATOR


@pytest.fixture(scope="session")
def golden():
    with open(
        os.path.join(os.path.dirname(__file__), "golden_chaplinsky.json"),
        encoding="utf8",
    ) as fp:
        return set(json.load(fp))
