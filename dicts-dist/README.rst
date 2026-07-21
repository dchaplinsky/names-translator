names-translator-dicts-uk
=========================

Compiled uk->ru name dictionaries for the `names_translator
<https://github.com/dchaplinsky/names-translator>`_ package: ~146,000
Ukrainian first names, last names and patronymics with their ranked Russian
translations, mined from real-world data and validated.

The data is stored as per-category DAWG files (the pymorphy3 approach) plus
compact rule tables: ~2.8 MB on disk, loaded lazily in well under 100 ms.
Built with ``python -m names_translator.dict_compiler`` from the main
repository; see
``names_translator_dicts_uk/data/manifest.json`` for sources, checksums and
build options.

Installation
------------

.. code-block:: bash

    $ pip install names_translator names-translator-dicts-uk

That is all: ``names_translator`` discovers this package automatically and
prefers it over the bundled legacy ``ua2ru.csv`` dictionary (which remains
as a fallback for names not covered here).
