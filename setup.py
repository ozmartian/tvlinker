#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from setuptools import setup, find_packages
from codecs import open
from os import path
from re import match


here = path.abspath(path.dirname(__file__))

def get_version(filename='__init__.py'):
    with open(path.join(here, filename), encoding='utf-8') as initfile:
        for line in initfile.readlines():
            m = match('__version__ *= *[\'](.*)[\']', line)
            if m:
                return m.group(1)

def get_description(filename='README.md'):
    with open(path.join(here, filename), encoding='utf-8') as f:
        return f.read()

setup(
    name='tvlinker',
    version=get_version(),
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='tv-release.net scraper integrated with real-debrid and various Linux & Windows download managers',
    long_description=get_description(),
    url='https://github.com/ozmartian/tvlinker',
    license='GPLv3+',

    packages=['tvlinker'],

    package_dir={'tvlinker': '.'},
    
    setup_requires=['setuptools >= 28.1.0'],
    
    install_requires=[
        'PyQt5 >= 5.7',
        'beautifulsoup4 >= 4.5.1',
    ] + ['lxml >= 3.6.4'] if 'win32' not in sys.platform else [],
    
    package_data={
        'tvlinker': ['tvlinker.ini']
    },

    entry_points={
        'gui_scripts': [
            'tvlinker = tvlinker.main:main'
        ]
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Topic :: Communications :: File Sharing',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    keywords='tvlinker scraping tv-release filesharing'

)