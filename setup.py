#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path
from re import match

from setuptools import setup

here = path.abspath(path.dirname(__file__))


def get_version(filename='__init__.py'):
    with open(path.join(here, filename), 'r') as initfile:
        for line in initfile.readlines():
            m = match('__version__ *= *[\'](.*)[\']', line)
            if m:
                return m.group(1)


def get_description(filename='README.md'):
    with open(path.join(here, filename), 'r') as f:
        file = list(f)
    desc = ''
    for item in file[8: len(file)]:
        desc += item
    return desc


def get_data_files():
    if sys.platform.startswith('linux'):
        return [
            ('/usr/share/pixmaps', ['data/pixmaps/vidcutter.png']),
            ('/usr/share/applications', ['data/desktop/vidcutter.desktop'])
        ]
    else:
        return []


setup(
    name='tvlinker',
    version=get_version(),
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='''tv-release.net link scraper integrated with real-debrid to unrestrict links + supporting
                   Aria2 RPC Daemon (windows/linux), kget (linux), pyLoad (windows/linux), Internet Download Manager
                   (windows). A built-in downloader is enabled by default.''',
    long_description=get_description(),
    url='http://tvlinker.ozmartians.com',
    license='GPLv3+',
    packages=['tvlinker'],
    package_dir={'tvlinker': '.'},
    setup_requires=['setuptools >= 26.1.1'],
    install_requires=['beautifulsoup4', 'QtAwesome'],
    extras_require={':sys_platform!="win32"': ['lxml']},
    package_data={'tvlinker': ['tvlinker.ini', 'assets/images/tvlinker.ico', 'assets/images/tvlinker.png']},
    entry_points={'gui_scripts': ['tvlinker = tvlinker.tvlinker:main']},
    keywords='tvlinker scraping tv-release filesharing internet',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Communications :: File Sharing',
        'Programming Language :: Python :: 3.5'
    ]
)
