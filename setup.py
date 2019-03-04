# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open as codecs_open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs_open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'flightline',
    version = '0.1',
    description = 'Python module to manage aerial operations using ESRI ArcMap',
    long_description = 'This module consists of a set of tools/functions to help with the management of aerial operations',

    url = 'https://github.com/OSPRI-GIS/flightline',
    author = 'OSPRI',
    author_email = 'gis@ospri.co.nz',

    license = 'GNU General Public License v3.0',

    classifiers = ['Development Status :: 3 - Alpha',
                   'Intended Audience :: End Users',
                   'Topic :: Aerial Operational Management',
                   'License :: GNU General Public License v3.0',
                   'Programming Language :: Python :: 2.7.1'],

    keywords = 'Aerial Tracmap OSPRI',
    packages = find_packages(exclude=['DOC','Documentation','tests']),
    install_requires = []
    )