names-translator
================

That's a small tool to generate as many possible transliteration options for ukrainian names.
First it translates the name into russian using a dictionary, then transliterates ukrainian and russian names
using the translitua package and 28 different transliteration tables. Finally, some heuristic is applied to cover
usual transliterations for well known names, which aren't covered by the transliteration tables.

Installation
==================================
Install from PyPI.

.. code-block:: bash

    $ pip install names_translator

Bigger dictionaries
==================================

The bundled ``ua2ru.csv`` covers ~19k names. For much better coverage install
the optional data package: ~146k validated first names, last names and
patronymics with ranked Russian translations, compiled into DAWG dictionaries
(the pymorphy3 approach):

.. code-block:: bash

    $ pip install names-translator-dicts-uk

``names_translator`` discovers it automatically and prefers it over the
legacy dictionary, which remains as a fallback for uncovered names. Ranked
lookups are also available directly:

.. code-block:: python

    >>> from names_translator.dicts import NameDicts
    >>> NameDicts().lookup("Дмитро", "first")
    ['Дмитрий', 'Дмитро']

Compared to loading the same 149k rows into a plain python dict (~300 ms,
+48 MB RSS), the compiled dictionaries load in 20-90 ms using ~4x less
memory (measured with ``tools/bench_dict_vs_dawg.py``). ``pip install
names_translator[fast]`` swaps the pure-python DAWG reader for the C
extension (~9x faster lookups, ~1M/s).

The dictionaries are compiled with ``python -m names_translator.dict_compiler``
(requires the ``DAWG2`` builder, e.g. via ``names_translator[fast]``); sources,
thresholds and checksums are recorded in the shipped ``manifest.json``.

Usage
==================================

.. code-block:: python

    >>> from names_translator import Transliterator
    >>> tr = Transliterator()
    >>> tr.transliterate("Чаплинський", "Дмитро", "Олександрович")
        {"Chaplins'kij Dmitro Oleksandrovich",
         'Chaplinski Dmitri Aleksandrovich',
         'Chaplinskii Dmitrii Aleksandrovich',
         'Chaplinskij Dmitrij Aleksandrovich',
         'Chaplinskijj Dmitrijj Aleksandrovich',
         'Chaplinskiy Dimitry Aleksandrovich',
         'Chaplinskiy Dmitriy Aleksandrovich',
         'Chaplinskiy Dmitriy Alexandrovich',
         'Chaplinskiy Dmitry Aleksandrovich',
         'Chaplinskiĭ Dmitriĭ Aleksandrovich',
         'Chaplinsky Dmitry Aleksandrovich',
         'Chaplinskyy Dmitryy Aleksandrovich',
         "Chaplyns'cyi Dmytro Olecsandrovych",
         "Chaplyns'kyi Dmytro Oleksandrovych",
         "Chaplyns'kyj Dmytro Oleksandrovych",
         "Chaplyns'kyy Dmytro Oleksandrovych",
         'Chaplynsjkyj Dmytro Oleksandrovych',
         'Chaplynski Dmytro Oleksandrovych',
         'Chaplynsky Dmytro Oleksandrovych',
         'Chaplynskyi Dimitry Oleksandrovych',
         'Chaplynskyi Dmitry Oleksandrovych',
         'Chaplynskyi Dmytro Oleksandrovych',
         'Chaplynskyi Dmytro Olexandrovych',
         'Chaplynskyy Dmytro Oleksandrovych',
         'Chaplynsʹkyĭ Dmytro Oleksandrovych',
         'Chaplȳnskȳĭ Dmȳtro Oleksandrovȳch',
         'Tchaplynskyy Dmytro Oleksandrovytch',
         'Tschaplynskyj Dmytro Oleksandrowytsch',
         "Čaplins'kij Dmitro Oleksandrovič",
         'Čaplinskij Dmitrij Aleksandrovič',
         'Čaplins′kij Dmitro Oleksandrovič',
         'Čaplynsjkyj Dmytro Oleksandrovyč',
         'Čaplynsʹkyj Dmytro Oleksandrovyč',
         'Чаплинский Дмитрий Александрович',
         'Чаплинський Дмитро Олександрович'}
