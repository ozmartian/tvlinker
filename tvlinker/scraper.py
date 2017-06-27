#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import requests
from bs4 import BeautifulSoup
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QThread, Qt
from PyQt5.QtWidgets import QMessageBox
from requests import HTTPError

from tvlinker.threads import ShadowSocks


class ScrapeManager(QObject):
    def __init__(self, source_url: str, user_agent: str, parent=None):
        super(ScrapeManager, self).__init__(parent)
        self.parent = parent
        self.source_url = source_url
        self.user_agent = user_agent
        self.workers = list()

    def add_scraper(self, start: int, end: int) -> bool:
        scrapeThread = QThread(self)
        scrapeWorker = ScrapeWorker(self.source_url, self.user_agent, start, end)
        scrapeThread.started.connect(self.show_progress)
        scrapeThread.started.connect(scrapeWorker.begin)
        scrapeWorker.moveToThread(scrapeThread)
        scrapeWorker.addRow.connect(self.add_row)
        scrapeWorker.workFinished.connect(self.scrape_finished)
        scrapeWorker.workFinished.connect(scrapeWorker.deleteLater, Qt.DirectConnection)
        scrapeWorker.workFinished.connect(scrapeThread.quit, Qt.DirectConnection)
        scrapeThread.finished.connect(scrapeThread.deleteLater, Qt.DirectConnection)
        self.workers.append(scrapeThread)
        return True


class ScrapeWorker(QObject):
    addRow = pyqtSignal(list)
    workFinished = pyqtSignal()

    def __init__(self, url: str, agent: str, start: int, end: int):
        super(ScrapeWorker, self).__init__()
        self.source_url = url
        self.user_agent = agent
        self.start_page = start
        self.end_page = end
        self.proxy = ShadowSocks.proxy()
        self.complete = False

    def scrape(self, pagenum: int) -> None:
        try:
            url = self.source_url.format(pagenum)
            req = requests.get(url, headers={'User-Agent': self.user_agent}, proxies=self.proxy)
            bs = BeautifulSoup(req.text, 'lxml')
            posts = bs('div', class_='post')
            for post in posts:
                dlsize = post.find('h2').get_text().strip()
                table_row = [
                    post.find('div', class_='p-c p-c-time').get_text().strip(),
                    post.find('a', class_='p-title').get('href').strip(),
                    post.find('a', class_='p-title').get_text().strip(),
                    dlsize[dlsize.rfind('(') + 1:len(dlsize) - 1]
                ]
                self.addRow.emit(table_row)
        except HTTPError:
            sys.stderr.write(sys.exc_info()[0])
            QMessageBox.critical(self, 'ERROR NOTIFICATION', sys.exc_info()[0])
            # self.exit()

    @pyqtSlot()
    def begin(self):
        for page in range(self.startpage, self.endpage):
            if QThread.currentThread().isInterruptionRequested():
                self.parent.interrupt()
                return
            self.scrape(page)
        self.complete = True
        self.workFinished.emit()
