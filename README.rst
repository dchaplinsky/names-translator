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

Dictionaries
==================================

The package bundles compiled DAWG dictionaries (the pymorphy3 approach):
~146k validated first names, last names and patronymics with ranked Russian
translations, plus a legacy pool of ~19k names from the historical ua2ru
dictionary used as a fallback for names the validated data does not cover.
Everything works out of the box; ranked lookups are also available directly:

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
         'Chaplinski Dmitri Oleksandrovich',
         'Chaplinski Dmitro Aleksandrovich',
         'Chaplinski Dmitro Oleksandrovich',
         'Chaplinskii Dmitrii Aleksandrovich',
         'Chaplinskii Dmitrii Oleksandrovich',
         'Chaplinskii Dmitro Aleksandrovich',
         'Chaplinskii Dmitro Oleksandrovich',
         'Chaplinskij Dmitrij Aleksandrovich',
         'Chaplinskij Dmitrij Oleksandrovich',
         'Chaplinskij Dmitro Aleksandrovich',
         'Chaplinskij Dmitro Oleksandrovich',
         'Chaplinskijj Dmitrijj Aleksandrovich',
         'Chaplinskijj Dmitrijj Oleksandrovich',
         'Chaplinskijj Dmitro Aleksandrovich',
         'Chaplinskijj Dmitro Oleksandrovich',
         'Chaplinskiy Dimitry Aleksandrovich',
         'Chaplinskiy Dimitry Oleksandrovich',
         'Chaplinskiy Dmitriy Aleksandrovich',
         'Chaplinskiy Dmitriy Alexandrovich',
         'Chaplinskiy Dmitriy Oleksandrovich',
         'Chaplinskiy Dmitriy Olexandrovich',
         'Chaplinskiy Dmitro Aleksandrovich',
         'Chaplinskiy Dmitro Alexandrovich',
         'Chaplinskiy Dmitro Oleksandrovich',
         'Chaplinskiy Dmitro Olexandrovich',
         'Chaplinskiy Dmitry Aleksandrovich',
         'Chaplinskiy Dmitry Oleksandrovich',
         'Chaplinskiĭ Dmitriĭ Aleksandrovich',
         'Chaplinskiĭ Dmitriĭ Oleksandrovich',
         'Chaplinskiĭ Dmitro Aleksandrovich',
         'Chaplinskiĭ Dmitro Oleksandrovich',
         'Chaplinsky Dmitro Aleksandrovich',
         'Chaplinsky Dmitro Oleksandrovich',
         'Chaplinsky Dmitry Aleksandrovich',
         'Chaplinsky Dmitry Oleksandrovich',
         'Chaplinskyy Dmitro Aleksandrovich',
         'Chaplinskyy Dmitro Oleksandrovich',
         'Chaplinskyy Dmitryy Aleksandrovich',
         'Chaplinskyy Dmitryy Oleksandrovich',
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
         'Čaplinskij Dmitrij Oleksandrovič',
         'Čaplinskij Dmitro Aleksandrovič',
         'Čaplinskij Dmitro Oleksandrovič',
         'Čaplins′kij Dmitro Oleksandrovič',
         'Čaplynsjkyj Dmytro Oleksandrovyč',
         'Čaplynsʹkyj Dmytro Oleksandrovyč',
         'Чаплинский Дмитрий Александрович',
         'Чаплинский Дмитрий Олександрович',
         'Чаплинский Дмитро Александрович',
         'Чаплинский Дмитро Олександрович',
         'Чаплинський Дмитро Олександрович'}
