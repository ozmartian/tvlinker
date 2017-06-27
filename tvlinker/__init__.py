#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtCore import QFileInfo


__version__ = '4.0.0'
__packager__ = 'pypi' # (pypi, arch, deb, rpm)

sys.path.insert(0, QFileInfo(__file__).absolutePath())
