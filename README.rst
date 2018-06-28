names-translator
================

That's a small tool to generate as many possible transliteration options for ukrainian names
First it translates the name into russian using dictionary, then transliterates ukrainian and russian names
using translit-ua package and 19 different transliteration tables. Finally, some heuristic is applied to cover
usual usual trasnliterations for well known names, which aren't covered by the transliteration tables

Installation
==================================
Install from PyPI.

.. code-block:: bash

    $ pip install names_translator

Usage
==================================

.. code-block:: python

    >>> from names_translator import Transliterator
    >>> tr = Transliterator()
    >>> tr.transliterate("Чаплинський", "Дмитро", "Олександрович")
        {"Chaplins'kij Dmitro Oleksandrovich",
         'Chaplinski Dmitri Aleksandrovich',
         'Chaplinskii Dimitry Aleksandrovich',
         'Chaplinskii Dmitrii Aleksandrovich',
         'Chaplinskii Dmitrii Alexandrovich',
         'Chaplinskii Dmitry Aleksandrovich',
         'Chaplinskij Dmitrij Aleksandrovich',
         'Chaplinskiy Dmitriy Aleksandrovich',
         'Chaplinsky Dmitry Aleksandrovich',
         "Chaplyns'cyi Dmytro Olecsandrovych",
         "Chaplyns'kyi Dmytro Oleksandrovych",
         "Chaplyns'kyj Dmytro Oleksandrovych",
         "Chaplyns'kyy Dmytro Oleksandrovych",
         'Chaplynski Dmytro Oleksandrovych',
         'Chaplynsky Dmytro Oleksandrovych',
         'Chaplynskyi Dimitry Oleksandrovych',
         'Chaplynskyi Dmitry Oleksandrovych',
         'Chaplynskyi Dmytro Oleksandrovych',
         'Chaplynskyi Dmytro Olexandrovych',
         'Chaplȳnskȳĭ Dmȳtro Oleksandrovȳch',
         'Tchaplynskyy Dmytro Oleksandrovytch',
         'Tschaplynskyj Dmytro Oleksandrowytsch',
         "Čaplins'kij Dmitro Oleksandrovič",
         'Čaplins′kij Dmitro Oleksandrovič',
         'Čaplynsʹkyj Dmytro Oleksandrovyč',
         'Чаплинский Дмитрий Александрович',
         'Чаплинський Дмитро Олександрович'}
