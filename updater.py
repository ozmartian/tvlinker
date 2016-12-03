#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.request import Request, urlopen
from urllib.parse import urlencode

from PyQt5.QtWidgets import QWidget


class Updater(QWidget):
    def __init__(self, parent, update_url: str):
        super(Updater, self).__init__(parent)
        self.parent = parent
        self.update_url = update_url

    def update_check(self):
        pass
