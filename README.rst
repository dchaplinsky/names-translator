names-translator
===========

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

