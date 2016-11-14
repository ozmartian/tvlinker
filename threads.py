#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import requests
from PyQt5.QtCore import QSettings, QThread, pyqtSignal
from bs4 import BeautifulSoup, FeatureNotFound
from var_dump import var_dump


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


class RealDebridThread(QThread):
    unrestrictedLink = pyqtSignal(str)

    def __init__(self, settings: QSettings, api_url: str, link_url: str):
        QThread.__init__(self)
        self.api_url = api_url
        self.api_token = settings.value('realdebrid_apitoken')
        self.link_url = link_url

    def __del__(self):
        self.wait()

    def unrestrict_link(self):
        headers = {
            'Authorization': 'Bearer %s' % self.api_token,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache'
        }
        payload = urlencode({'link': self.link_url}).encode('utf-8')
        req = Request('%s/unrestrict/link' % self.api_url, headers=headers, data=payload)
        res = urlopen(req).read().decode('utf-8')
        jsonres = json.loads(res)
        if 'download' in jsonres.keys():
            self.unrestrictedLink.emit(jsonres['download'])

    def run(self) -> None:
        self.unrestrict_link()


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
        user, passwd = '', ''
        if len(self.rpc_username) > 0 and len(self.rpc_password) > 0:
            user = self.rpc_username
            passwd = self.rpc_password
        elif len(self.rpc_secret) > 0:
            user = 'token'  
            passwd = self.rpc_secret
        aria2_endpoint = '%s:%s/jsonrpc' % (self.rpc_host, self.rpc_port)
        headers = { 'Content-Type': 'application/json' }
        payload = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'aria2.addUri',
                             'params': ['%s:%s' % (user, passwd), [self.link_url]]}, sort_keys=False).encode('utf-8')
        req = Request(aria2_endpoint, headers=headers, data=payload)
        res = urlopen(req).read().decode('utf-8')
        jsonres = json.loads(res)
        if 'result' in jsonres.keys():
            self.aria2Confirmation.emit(True)
        else:
            var_dump(req)
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
        self.cancel_download = False

    def __del__(self) -> None:
        self.wait()

    def download_file(self) -> None:
        req = requests.get(self.download_link, stream=True)
        filesize = int(req.headers['Content-Length'])
        filename = os.path.basename(self.download_path)
        downloadedChunk = 0
        blockSize = 1024
        with open(self.download_path, 'wb') as f:
            for chunk in req.iter_content(chunk_size=blockSize):
                if self.cancel_download or not chunk:
                    req.close()
                    break
                f.write(chunk)
                downloadedChunk += len(chunk)
                progress = float(downloadedChunk) / filesize
                self.dlProgress.emit(progress * 100)
                progressTxt = '<b>Downloading {0}</b>:<br/>{1} <b>of</b> {3} <b>bytes</b> [{2:.2%}]'\
                    . format(filename, downloadedChunk, progress, filesize)
                self.dlProgressTxt.emit(progressTxt)
        self.dlComplete.emit()

    def run(self) -> None:
        self.download_file()
