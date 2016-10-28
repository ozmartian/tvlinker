#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
from urllib.request import Request, urlopen

from PyQt5.QtCore import QSettings, QThread, pyqtSignal
from bs4 import BeautifulSoup, FeatureNotFound


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
            req = Request(url, headers={'User-Agent': self.user_agent})
            res = urlopen(req)
            if sys.platform == 'win32':
                bs = BeautifulSoup(res.read(), 'html.parser')
            else:
                try:
                    bs = BeautifulSoup(res.read(), 'lxml')
                except FeatureNotFound:
                    bs = BeautifulSoup(res.read(), 'html.parser')
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
        req = Request(self.link_url, headers={'User-Agent': self.user_agent})
        res = urlopen(req)
        if sys.platform == 'win32':
            bs = BeautifulSoup(res.read(), 'html.parser')
        else:
            try:
                bs = BeautifulSoup(res.read(), 'lxml')
            except FeatureNotFound:
                bs = BeautifulSoup(res.read(), 'html.parser')
        dltable = bs.find('table', id='download_table').find_all('tr')
        for hoster_html in dltable:
            hosters.append([hoster_html.td.img.get('src'), hoster_html.find('td', class_='td_cols').a.get('href')])
        self.setHosters.emit(hosters)

    def run(self) -> None:
        self.get_hoster_links()


class Aria2Thread(QThread):

    aria2Confirmation = pyqtSignal(bool)

    def __init__(self, settings: QSettings, link_url: str):
        QThread.__init__(self)
        self.rpc_host = settings.value('aria2_rpc_host')
        self.rpc_port = settings.value('aria2_rpc_port')
        self.rpc_secret = settings.value('aria2_rpc_secret')
        self.rpc_username = settings.value('aria2_rpc_username')
        self.rpc_password = settings.value('aria2_rpc_password')
        self.link_url = link_url

    def __del__(self) -> None:
        self.wait()

    def add_uri(self) -> None:
        try:
            jsonreq = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'aria2.addUri',
                                  'params': ['token:%s' % self.rpc_secret, [self.link_url]]})
            conn = urlopen('%s:%s/jsonrpc' % (self.rpc_host, self.rpc_port), jsonreq.encode('utf-8'))
            jsonres = json.loads(conn.read().decode('utf-8'))
            if 'result' in jsonres.keys():
                if len(jsonres['result']) > 0:
                    self.aria2Confirmation.emit(True)
                    return
            self.aria2Confirmation.emit(False)
        except:
            print(sys.exc_info()[0])
            self.aria2Confirmation.emit(False)

    def run(self) -> None:
        self.add_uri()


class DownloadThread(QThread):

    dlComplete = pyqtSignal()
    dlProgress = pyqtSignal(int)
    dlProgressTxt = pyqtSignal(str)

    def __init__(self, link_url: str, dl_path: str):
        QThread.__init__(self)
        self.download_link = link_url
        self.download_path = dl_path

    def __del__(self) -> None:
        self.wait()

    def run(self) -> None:
        url = self.download_link
        rq = urlopen(url)
        fSize = int(rq.info()['Content-Length'])
        fileName = os.path.basename(self.download_path)
        downloadedChunk = 0
        blockSize = 2048
        with open(self.download_path, 'wb') as sura:
            while True:
                chunk = rq.read(blockSize)
                if not chunk:
                    break
                downloadedChunk += len(chunk)
                sura.write(chunk)
                progress = float(downloadedChunk) / fSize
                self.dlProgress.emit(progress * 100)
                progressTxt = '<b>Saving {0}</b>: {1} [{2:.2%}] <b>of</b> {3} <b>bytes</b>.'\
                    . format(fileName, downloadedChunk, progress, fSize)
                self.dlProgressTxt.emit(progressTxt)
        self.dlComplete.emit()
