#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time

from datetime import datetime, timedelta
from tzlocal import get_localzone

import pytz
import requests

from PyQt5.QtCore import QObject, QSettings, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, qApp
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError

import cloudscraper

from tvlinker.filesize import alternative, size

try:
    # noinspection PyPackageRequirements
    import simplejson as json
except ImportError:
    import json


class ShadowSocks:
    config = {
        'ssocks': {
            'procs': ['ss-qt5', 'sslocal'],
            'proxies': {
                'http': 'socks5://127.0.0.1:1080',
                'https': 'socks5://127.0.0.1:1080'
            },
        },
        'v2ray': {
            'procs': ['v2ray'],
            'proxies': {
                'http': 'socks5://127.0.0.1:10808',
                'https': 'socks5://127.0.0.1:10808'
            }
        }
    }

    @staticmethod
    def detect() -> str:
        if sys.platform.startswith('linux'):
            ptypes = ShadowSocks.config.keys()
            ps = os.popen('ps -Af').read()
            for ptype in ptypes:
                procs = ShadowSocks.config[ptype]['procs']
                for p in procs:
                    if ps.count(p):
                        return ptype
        return None

    @staticmethod
    def proxies() -> dict:
        proxy_type = ShadowSocks.detect()
        return ShadowSocks.config[proxy_type]['proxies'] if proxy_type is not None else {}


class ScrapeWorker(QObject):
    addRow = pyqtSignal(list)
    workFinished = pyqtSignal()

    def __init__(self, source_url: str, useragent: str, maxpages: int):
        super(ScrapeWorker, self).__init__()
        self.maxpages = maxpages
        self.source_url = source_url
        self.user_agent = useragent
        self.scraper = cloudscraper.create_scraper()
        self.scraper.proxies = ShadowSocks.proxies()
        self.tz_format = '%b %d %Y %H:%M'
        self.tz_local = get_localzone()
        self.complete = False

    def scrape(self, pagenum: int) -> None:
        try:
            url = self.source_url.format(pagenum + 1)
            req = self.scraper.get(url)
            bs = BeautifulSoup(req.text, 'lxml')
            posts = bs('div', class_='post')
            for post in posts:
                dt_utc = datetime.strptime(post.find('div', class_='p-c p-c-time').get_text().strip(), self.tz_format)
                # TODO: fix hardcoded DST adjustment
                dt_local = dt_utc.replace(tzinfo=pytz.utc).astimezone(self.tz_local) - timedelta(hours=1)
                dlsize = post.find('h2').get_text().strip()
                table_row = [
                    dt_local.strftime(self.tz_format),
                    post.find('a', class_='p-title').get('href').strip(),
                    post.find('a', class_='p-title').get_text().strip(),
                    dlsize[dlsize.rfind('(') + 1:len(dlsize) - 1]
                ]
                self.addRow.emit(table_row)
        except HTTPError:
            sys.stderr.write(sys.exc_info()[0])
            # noinspection PyTypeChecker
            QMessageBox.critical(None, 'ERROR NOTIFICATION', sys.exc_info()[0])
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
    setHosters = pyqtSignal(list)
    noLinks = pyqtSignal()

    def __init__(self, link_url: str, useragent: str):
        QThread.__init__(self)
        self.link_url = link_url
        self.user_agent = useragent
        self.scraper = cloudscraper.create_scraper()
        self.scraper.proxies = ShadowSocks.proxies()

    def __del__(self) -> None:
        self.wait()

    def get_hoster_links(self) -> None:
        try:
            req = self.scraper.get(self.link_url)
            bs = BeautifulSoup(req.text, 'lxml')
            links = bs.select('div.post h2[style="text-align: center;"]')
            self.setHosters.emit(links)
        except HTTPError:
            print(sys.exc_info()[0])
            # noinspection PyTypeChecker
            QMessageBox.critical(None, 'ERROR NOTIFICATION', sys.exc_info()[0])
            QThread.currentThread().quit()
        except IndexError:
            self.noLinks.emit()
            QThread.currentThread().quit()

    def run(self) -> None:
        self.get_hoster_links()


class RealDebridThread(QThread):
    unrestrictedLink = pyqtSignal(str)
    supportedHosts = pyqtSignal(dict)
    hostStatus = pyqtSignal(dict)
    errorMsg = pyqtSignal(list)

    class RealDebridAction:
        UNRESTRICT_LINK = 0,
        SUPPORTED_HOSTS = 1,
        HOST_STATUS = 2

    def __init__(self,
                 settings: QSettings,
                 api_url: str,
                 link_url: str,
                 action: RealDebridAction = RealDebridAction.UNRESTRICT_LINK,
                 check_host: str = None):
        QThread.__init__(self)
        self.api_url = api_url
        self.api_token = settings.value('realdebrid_apitoken')
        self.api_proxy = settings.value('realdebrid_apiproxy', False, bool)
        self.link_url = link_url
        self.action = action
        self.check_host = check_host
        self.proxies = ShadowSocks.proxies() if self.api_proxy else {}

    def __del__(self):
        self.wait()

    def post(self, endpoint: str, payload: object = None) -> dict:
        try:
            res = requests.post('{0}{1}?auth_token={2}'.format(self.api_url, endpoint, self.api_token),
                                data=payload, proxies=self.proxies)
            return res.json()
        except HTTPError:
            print(sys.exc_info())
            self.errorMsg.emit([
                'ERROR NOTIFICATION',
                '<h3>Real-Debrid API Error</h3>'
                'A problem occurred whilst communicating with Real-Debrid. Please check your '
                'Internet connection.<br/><br/>'
                '<b>ERROR LOG:</b><br/>(Error Code %s) %s<br/>%s' %
                (qApp.applicationName(), HTTPError.code, HTTPError.reason)
            ])
            # self.exit()

    def unrestrict_link(self) -> None:
        jsonres = self.post(endpoint='/unrestrict/link', payload={'link': self.link_url})
        if 'download' in jsonres.keys():
            self.unrestrictedLink.emit(jsonres['download'])
        else:
            self.errorMsg.emit([
                'REALDEBRID ERROR',
                '<h3>Could not unrestrict link</h3>The hoster is most likely '
                'down, please try again later.<br/><br/>{}'.format(jsonres)
            ])

    def supported_hosts(self) -> None:
        jsonres = self.post(endpoint='/hosts')
        self.supportedHosts.emit(jsonres)

    # def host_status(self, host: str) -> None:
    #     jsonres = self.post(endpoint='/hosts/status')
    #     self.hostStatus.emit(jsonres)

    def run(self) -> None:
        if self.action == RealDebridThread.RealDebridAction.UNRESTRICT_LINK:
            self.unrestrict_link()
        elif self.action == RealDebridThread.RealDebridAction.SUPPORTED_HOSTS:
            self.supported_hosts()
        # elif self.action == RealDebridThread.HOST_STATUS:
        #     self.host_status(self.check_host)


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
        payload = json.dumps(
            {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'aria2.addUri',
                'params': ['%s:%s' % (user, passwd), [self.link_url]]
            },
            sort_keys=False).encode('utf-8')
        try:
            from urllib.parse import urlencode
            from urllib.request import Request, urlopen
            req = Request(aria2_endpoint, headers=headers, data=payload)
            res = urlopen(req).read().decode('utf-8')
            jsonres = json.loads(res)
            # res = requests.post(aria2_endpoint, headers=headers, data=payload)
            # jsonres = res.json()
            self.aria2Confirmation.emit('result' in jsonres.keys())
        except HTTPError:
            print(sys.exc_info())
            # noinspection PyTypeChecker
            QMessageBox.critical(None, 'ERROR NOTIFICATION', sys.exc_info(), QMessageBox.Ok)
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
        self.proxies = ShadowSocks.proxies()

    def __del__(self) -> None:
        self.wait()

    def download_file(self) -> None:
        req = requests.get(self.download_link, stream=True, proxies=self.proxies)
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
                dlspeed = downloadedChunk // (time.clock() - start) / 1000
                progressTxt = '<b>Downloading {0}</b>:<br/>{1} of <b>{3}</b> [{2:.2%}] [{4} kbps]' \
                    .format(filename, downloadedChunk, progress, size(filesize, system=alternative), dlspeed)
                self.dlProgressTxt.emit(progressTxt)
        self.dlComplete.emit()

    def run(self) -> None:
        self.download_file()
