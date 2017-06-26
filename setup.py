#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from codecs import open
from os import path
from re import match

from setuptools import setup


def get_value(varname, filename='tvlinker/__init__.py'):
    with open(path.join(here, filename), encoding='utf-8') as initfile:
        for line in initfile.readlines():
            m = match('__%s__ *= *[\'](.*)[\']' % varname, line)
            if m:
                return m.group(1)


def get_description(filename='README.md'):
    with open(path.join(here, filename), encoding='utf-8') as f:
        file = list(f)
    desc = ''
    for item in file[8: len(file)]:
        desc += item
    return desc


def get_install_requires():
    if packager == 'pypi':
        return ['PyQt5', 'beautifulsoup4', 'lxml', 'requests', 'requests[socks]', 'cfscrape']
    else:
        return ['cfscrape', 'requests[socks]']


def get_data_files():
    files = []
    if sys.platform.startswith('linux'):
        return [
            ('/usr/share/pixmaps', ['data/icons/tvlinker.png']),
            ('/usr/share/applications', ['data/desktop/tvlinker.desktop'])
        ]
    return files


here = path.abspath(path.dirname(__file__))

packager = get_value('packager')

setup(
    name='tvlinker',
    version=get_value('version'),
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='''Scene-RLS TV show link scraper integrated w/ real-debrid to unrestrict links + support for download
                   managers: Built-in (window/linux), Aria2 RPC Daemon (windows/linux), Internet Download Manager 
                   (windows), KGet (linux), pyLoad (windows/linux), and Persepolis (windows/linux)''',
    long_description=get_description(),
    url='http://tvlinker.ozmartians.com',
    license='GPLv3+',

    packages=['tvlinker'],

    package_dir={'tvlinker': 'tvlinker'},

    setup_requires=['setuptools'],

    install_requires=get_install_requires(),

    package_data={ 'tvlinker': ['README.md', 'LICENSE', 'tvlinker/tvlinker.ini'] },

    data_files=get_data_files(),

    entry_points={'gui_scripts': ['tvlinker = tvlinker.__main__:main']},

    keywords='tvlinker scraping tv-release filesharing internet',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Communications :: File Sharing',
        'Programming Language :: Python :: 3 :: Only'
    ]
)
