#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup


setup(
    name='tvlinker',
    version='1.0',
    packages=[''],
    url='https://github.com/ozmartian/tvlinker',
    license='GPLv3+',
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='Link scraper d/l intgration for tv-release.net',
    requires=[
        'PyQt5',

    ]
)


setup(
    name='QtWaitingSpinner',
    version='1.0',
    packages=[''],
    url='https://github.com/z3ntu/QtWaitingSpinner',
    license='MIT',
    author='Luca Weiss',
    author_email='WEI16416@spengergasse.at',
    description='A waiting spinner for PyQt5', requires=['PyQt5']
)
