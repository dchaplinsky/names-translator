import names_translator

from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

requirements = [
    'translitua==1.2.4',
]

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='names_translator',

    version=names_translator.__version__,

    description='Automatic translation and transliteration of ukrainian names into Russian and English + some extra tools to deal with mixed languages, etc',
    long_description=long_description,

    url='https://github.com/dchaplinsky/names-translator',

    author='dchaplinsky',
    author_email='chaplinsky.dmitry@gmail.com',

    license='MIT',
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Natural Language :: Ukrainian',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: General',
        'Topic :: Text Processing :: Indexing',
    ],

    keywords='ukrainian names translation transliteration',

    packages=[
        'names_translator',
    ],

    # data_files=[('names_translator/data', ['ua2ru.csv'])],
    include_package_data=True,

    package_data={'': ['LICENSE']},
)
