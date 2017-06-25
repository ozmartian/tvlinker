#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import time

import cfscrape
import requests

from PyQt5.QtCore import QObject, QSettings, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, qApp
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
from urllib.request import Request, urlopen

from tvlinker.filesize import size, alternative


class ShadowSocks:
    @staticmethod
    def is_running(process='ss-qt5') -> bool:
        if sys.platform.startswith('linux'):
            return os.popen('ps -Af').read().count(process) > 0
        else:
            return False

    @staticmethod
    def proxy() -> dict:
        return dict(http='socks5://127.0.0.1:1080', https='socks5://127.0.0.1:1080')\
            if ShadowSocks.is_running() else dict()


class ScrapeWorker(QObject):
    addRow = pyqtSignal(list)
    workFinished = pyqtSignal()

    def __init__(self, source_url: str, useragent: str, maxpages: int):
        super(ScrapeWorker, self).__init__()
        self.maxpages = maxpages
        self.source_url = source_url
        self.user_agent = useragent
        self.proxy = ShadowSocks.proxy()
        self.complete = False

    def scrape(self, pagenum: int) -> None:
        try:
            url = self.source_url.format(pagenum + 1)
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
        for page in range(self.maxpages):
            if QThread.currentThread().isInterruptionRequested():
                return
            self.scrape(page)
        self.complete = True
        self.workFinished.emit()


class HostersThread(QThread):
    setHosters = pyqtSignal(list, list)

    def __init__(self, link_url: str, useragent: str):
        QThread.__init__(self)
        self.link_url = link_url
        self.user_agent = useragent
        self.proxy = ShadowSocks.proxy()
        self.scraper = cfscrape.create_scraper()

    def __del__(self) -> None:
        self.wait()

    def get_hoster_links(self) -> None:
        hosters = list()
        try:
            req = self.scraper.get(self.link_url, proxies=self.proxy)
            bs = BeautifulSoup(req.text, 'lxml')
            titles = bs.select('div.post p[style="text-align: center;"]')
            del titles[0]
            links = bs.select('div.post h2[style="text-align: center;"]')
            for title in titles:
                link = links[titles.index(title)]
            self.setHosters.emit(titles, links)
        except HTTPError:
            print(sys.exc_info()[0])
            QMessageBox.critical(self, 'ERROR NOTIFICATION', sys.exc_info()[0])
            # self.exit()

    def run(self) -> None:
        self.get_hoster_links()


class RealDebridThread(QThread):
    unrestrictedLink = pyqtSignal(str)
    supportedHosts = pyqtSignal(dict)
    hostStatus = pyqtSignal(dict)

    class RealDebridAction:
        UNRESTRICT_LINK = 0,
        SUPPORTED_HOSTS = 1,
        HOST_STATUS = 2

    def __init__(self, settings: QSettings, api_url: str, link_url: str,
                 action: RealDebridAction = RealDebridAction.UNRESTRICT_LINK, check_host: str = None):
        QThread.__init__(self)
        self.api_url = api_url
        self.api_token = settings.value('realdebrid_apitoken')
        self.link_url = link_url
        self.action = action
        self.check_host = check_host
        self.proxy = ShadowSocks.proxy()

    def __del__(self):
        self.wait()

    def connect(self, endpoint: str, payload: object=None) -> object:
        try:
            headers = {
                'Authorization': 'Bearer %s' % self.api_token,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cache-Control': 'no-cache'
            }
            res = requests.post('%s%s' % (self.api_url, endpoint), headers=headers, data=payload,
                                proxies=self.proxy, verify=False)
            return res.json()
        except HTTPError:
            print(sys.exc_info())
            QMessageBox.critical(self, 'ERROR NOTIFICATION',
                                 '<h3>Real-Debrid API Error</h3>' +
                                 'A problem occurred whilst communicating with Real-Debrid. Please check your '
                                 'Internet connection.<br/><br/>' +
                                 '<b>ERROR LOG:</b><br/>(Error Code %s) %s<br/>%s'
                                 % (qApp.applicationName(), HTTPError.code, HTTPError.reason), QMessageBox.Ok)
            # self.exit()

    def unrestrict_link(self) -> None:
        jsonres = self.connect(endpoint='/unrestrict/link', payload={'link': self.link_url})
        # if 'download' in jsonres.keys():
        self.unrestrictedLink.emit(jsonres['download'])

    def supported_hosts(self) -> None:
        jsonres = self.connect(endpoint='/hosts')
        self.supportedHosts.emit(jsonres)

    def host_status(self, host: str) -> None:
        jsonres = self.connect(endpoint='/hosts/status')
        self.hostStatus.emit(jsonres)

    def run(self) -> None:
        if self.action == RealDebridThread.RealDebridAction.UNRESTRICT_LINK:
            self.unrestrict_link()
        elif self.action == RealDebridThread.RealDebridAction.SUPPORTED_HOSTS:
            self.supported_hosts()
        elif self.action == RealDebridThread.HOST_STATUS:
            self.host_status(self.check_host)


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
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'aria2.addUri',
                              'params': ['%s:%s' % (user, passwd), [self.link_url]]},
                             sort_keys=False).encode('utf-8')
        try:
            req = Request(aria2_endpoint, headers=headers, data=payload)
            res = urlopen(req).read().decode('utf-8')
            jsonres = json.loads(res)
            # res = requests.post(aria2_endpoint, headers=headers, data=payload)
            # jsonres = res.json()
            self.aria2Confirmation.emit('result' in jsonres.keys())
        except HTTPError:
            print(sys.exc_info())
            QMessageBox.critical(self, 'ERROR NOTIFICATION', sys.exc_info(), QMessageBox.Ok)
            self.aria2Confirmation.emit(False)
            # self.exit()

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
        self.proxy = ShadowSocks.proxy()

    def __del__(self) -> None:
        self.wait()

    def download_file(self) -> None:
        req = requests.get(self.download_link, stream=True, proxies=self.proxy)
        filesize = int(req.headers['Content-Length'])
        filename = os.path.basename(self.download_path)
        downloadedChunk = 0
        blockSize = 8192
        start = time.clock()
        with open(self.download_path, 'wb') as f:
            for chunk in req.iter_content(chunk_size=blockSize):
                if self.cancel_download or not chunk:
                    req.close()
                    break
                f.write(chunk)
                downloadedChunk += len(chunk)
                progress = float(downloadedChunk) / filesize
                self.dlProgress.emit(progress * 100)
                dlspeed = downloadedChunk//(time.clock() - start) / 1000
                progressTxt = '<b>Downloading {0}</b>:<br/>{1} of <b>{3}</b> [{2:.2%}] [{4} kbps]' \
                    .format(filename, downloadedChunk, progress, size(filesize, system=alternative), dlspeed)
                self.dlProgressTxt.emit(progressTxt)
        self.dlComplete.emit()

    def run(self) -> None:
        self.download_file()
