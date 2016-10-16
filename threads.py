#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from urllib.request import Request, urlopen

from PyQt5.QtCore import QSettings, QThread, pyqtSignal
from bs4 import BeautifulSoup


class ScrapeThread(QThread):

    addRow = pyqtSignal(list)

    def __init__(self, settings: QSettings, maxpages: int = 10):
        QThread.__init__(self)
        self.source_url = settings.value('source_url')
        self.user_agent = settings.value('user_agent')
        self.maxpages = maxpages

    def __del__(self) -> None:
        self.wait()

    def scrape_links(self) -> None:
        row = 0
        for page in range(1, self.maxpages + 1):
            url = self.source_url % page
            req = Request(url, headers={'User-agent': self.user_agent})
            res = urlopen(req)
            if sys.platform == 'win32':
                bs = BeautifulSoup(res.read(), 'html.parser')
            else:
                bs = BeautifulSoup(res.read(), 'lxml')
            links = bs.find_all('table', class_='posts_table')
            for link_table in links:
                cols = link_table.tr.find_all('td')
                table_row = [
                    cols[2].get_text().replace('\n', '').strip(),
                    cols[1].find('a').get('href').replace('\n', '').strip(),
                    cols[1].find('a').get_text().replace('\n', '').strip(),
                    cols[0].find('a').get_text().replace('TV-', '').replace('\n', '').strip()
                ]
                self.addRow.emit(table_row)
                row += 1

    def run(self) -> None:
        self.scrape_links()


class HostersThread(QThread):

    setHosters = pyqtSignal(list)

    def __init__(self, settings: QSettings, link_url: str):
        QThread.__init__(self)
        self.user_agent = settings.value('user_agent')
        self.link_url = link_url

    def __del__(self) -> None:
        self.wait()

    def get_hoster_links(self) -> None:
        hosters = []
        req = Request(self.link_url, headers={'User-agent': self.user_agent})
        res = urlopen(req)
        if sys.platform == 'win32':
            bs = BeautifulSoup(res.read(), 'html.parser')
        else:
            bs = BeautifulSoup(res.read(), 'lxml')
        dltable = bs.find('table', id='download_table').find_all('tr')
        for hoster_html in dltable:
            hosters.append([hoster_html.td.img.get('src'), hoster_html.find('td', class_='td_cols').a.get('href')])
        self.setHosters.emit(hosters)

    def run(self) -> None:
        self.get_hoster_links()
