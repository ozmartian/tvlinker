#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name='tvlinker',
    version='1.0',
    packages=['tvlinker'],
    url='https://github.com/ozmartian/tvlinker',
    license='GPLv3+',
    author='Pete Alexandrou',
    author_email='pete@ozmartians.com',
    description='Link scraper d/l intgration for tv-release.net',
    requires=[
        'PyQt5',
        'beautifulsoup4'
    ]
)
