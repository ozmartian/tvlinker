#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.client
import os
from urllib.parse import quote_plus

from PyQt5.QtCore import (QFile, QFileInfo, QJsonDocument, QModelIndex, QSettings, QSize,
                          Qt, QTextStream, QUrl, pyqtSlot)
from PyQt5.QtGui import (QCloseEvent, QColor, QDesktopServices, QFont, QFontDatabase,
                         QIcon, QPalette, QPixmap)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QMessageBox,
                             QProgressBar, QPushButton, QSizePolicy,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, qApp)

from hosters import HosterLinks
from pyload import PyloadConnection, PyloadConfig
from threads import HostersThread, ScrapeThread, Aria2Thread
import assets


class TVLinker(QDialog):
    def __init__(self, parent=None, f=Qt.Window):
        super(TVLinker, self).__init__(parent, f)
        self.rows, self.cols = 0, 0
        self.init_stylesheet()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 5)
        self.init_settings()
        layout.addLayout(self.init_form())
        layout.addWidget(self.init_table())
        layout.addLayout(self.init_metabar())
        self.setLayout(layout)
        self.setWindowTitle(qApp.applicationName())
        self.setWindowIcon(QIcon(self.get_path('images/tvlinker.png')))
        self.resize(1000, 750)
        self.show()
        self.start_scraping()
        self.hosters_win = HosterLinks(parent=self)
        self.hosters_win.downloadLink.connect(self.download_link)
        self.hosters_win.copyLink.connect(self.copy_download_link)

    def init_stylesheet(self) -> None:
        qApp.setStyle('Fusion')
        QFontDatabase.addApplicationFont(self.get_path('fonts/OpenSans.ttf'))
        qss = QFile(self.get_path('%s.qss' % qApp.applicationName().lower()))
        qss.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(qss)
        qApp.setStyleSheet(stream.readAll())

    def init_settings(self) -> None:
        self.settings_ini = self.get_path(path='%s.ini' % qApp.applicationName().lower(), override=True)
        self.settings_ini_secret = self.get_path(path='%s.ini.secret' % qApp.applicationName().lower(), override=True)
        self.settings_path = self.settings_ini_secret if os.path.exists(self.settings_ini_secret) else self.settings_ini
        self.settings = QSettings(self.settings_path, QSettings.IniFormat)
        self.source_url = self.settings.value('source_url')
        self.user_agent = self.settings.value('user_agent')
        self.dl_pagecount = int(self.settings.value('dl_pagecount'))
        self.dl_pagelinks = int(self.settings.value('dl_pagelinks'))
        self.realdebrid_api_token = self.settings.value('realdebrid_apitoken')
        self.download_manager = self.settings.value('download_manager')
        if self.download_manager == 'pyload':
            self.pyload_config = PyloadConfig()
            self.pyload_config.host = self.settings.value('pyload_host')
            self.pyload_config.username = self.settings.value('pyload_username')
            self.pyload_config.password = self.settings.value('pyload_password')
        elif self.download_manager == 'idm':
            self.idm_install_path = self.settings.value('idm_install_path')

    def init_form(self) -> QHBoxLayout:
        logo = QPixmap(self.get_path('images/tvrelease.png'))
        self.search_field = QLineEdit(self, clearButtonEnabled=True,
                                      placeholderText='Enter search criteria')
        self.search_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_field.textChanged.connect(self.filter_table)
        self.dlpages_field = QComboBox(self, toolTip='Pages', editable=False, cursor=Qt.PointingHandCursor)
        self.dlpages_field.addItems(('10', '20', '30', '40'))
        self.dlpages_field.setCurrentIndex(self.dlpages_field.findText(str(self.dl_pagecount), Qt.MatchFixedString))
        self.dlpages_field.currentIndexChanged.connect(self.update_pagecount)
        self.refresh_button = QPushButton(QIcon.fromTheme('view-refresh'), ' Refresh', cursor=Qt.PointingHandCursor,
                                          toolTip='Refresh', iconSize=QSize(12, 12), clicked=self.refresh_links)
        self.settings_button = QPushButton(self, flat=False, icon=QIcon(self.get_path('images/settings.png')),
                                           toolTip='Settings', cursor=Qt.PointingHandCursor, clicked=self.show_settings)
        layout = QHBoxLayout()
        layout.addWidget(QLabel(pixmap=logo.scaledToHeight(36, Qt.SmoothTransformation)))
        layout.addWidget(self.search_field)
        layout.addWidget(QLabel('Pages:'))
        layout.addWidget(self.dlpages_field)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.settings_button)
        return layout

    def init_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 4, self)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.hideColumn(1)
        self.table.setCursor(Qt.PointingHandCursor)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setHorizontalHeaderLabels(('Date', 'URL', 'Description', 'Format'))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(100)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.sortByColumn(0, Qt.DescendingOrder)
        self.table.doubleClicked.connect(self.show_hosters)
        return self.table

    def init_metabar(self) -> QHBoxLayout:
        self.meta_template = '<div>Total number of links retrieved: <b>%s</b></div>'
        self.progress = QProgressBar(parent=self, minimum=0, maximum=(self.dl_pagecount * self.dl_pagelinks), visible=False)
        palette = self.progress.palette()
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.Foreground, QColor(119, 89, 127))
        self.progress.setPalette(palette)
        self.meta_label = QLabel(textFormat=Qt.RichText, alignment=Qt.AlignRight, objectName='totals')
        self.meta_label.setFixedHeight(30)
        self.meta_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.update_metabar()
        layout = QHBoxLayout()
        layout.addWidget(self.progress, Qt.AlignLeft)
        layout.addWidget(self.meta_label, Qt.AlignRight)
        return layout

    @pyqtSlot()
    def show_settings(self) -> None:
        pass

    def update_metabar(self) -> bool:
        rowcount = self.table.rowCount()
        self.meta_label.setText(self.meta_template.replace('%s', str(rowcount)))
        self.progress.setValue(rowcount)
        return True

    def start_scraping(self, maxpages: int = 10) -> None:
        self.rows = 0
        qApp.setOverrideCursor(Qt.WaitCursor)
        if self.table.rowCount() > 0:
            self.table.clearContents()
            self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        self.scrape = ScrapeThread(settings=self.settings, maxpages=maxpages)
        self.scrape.addRow.connect(self.add_row)
        self.scrape.started.connect(self.progress.show)
        self.scrape.finished.connect(self.scrape_finished)
        self.progress.setValue(0)
        self.scrape.start()

    @pyqtSlot(bool)
    def refresh_links(self) -> None:
        self.start_scraping(int(self.dlpages_field.currentText()))

    @pyqtSlot(int)
    def update_pagecount(self, index: int) -> None:
        pagecount = int(self.dlpages_field.itemText(index))
        self.progress.setMaximum(pagecount * self.dl_pagelinks)
        self.start_scraping(pagecount)

    @pyqtSlot()
    def scrape_finished(self) -> None:
        self.progress.hide()
        self.table.setSortingEnabled(True)
        qApp.restoreOverrideCursor()

    @pyqtSlot(list)
    def add_row(self, row: list) -> None:
        self.cols = 0
        self.table.setRowCount(self.rows + 1)
        for item in row:
            table_item = QTableWidgetItem(item)
            table_item.setToolTip(row[1])
            table_item.setFont(QFont('Open Sans', weight=QFont.Normal))
            if self.cols == 2:
                table_item.setFont(QFont('Open Sans', weight=QFont.DemiBold))
                table_item.setText('  ' + table_item.text())
            elif self.cols == 3:
                table_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(self.rows, self.cols, table_item)
            self.update_metabar()
            self.cols += 1
        self.rows += 1

    @pyqtSlot(list)
    def add_hosters(self, hosters: list) -> None:
        self.hosters_win.show_hosters(hosters)

    @pyqtSlot(QModelIndex)
    def show_hosters(self, index: QModelIndex) -> bool:
        qApp.setOverrideCursor(Qt.BusyCursor)
        self.hosters_win.show()
        self.hosters_win.activateWindow()
        self.links = HostersThread(settings=self.settings, link_url=self.table.item(self.table.currentRow(), 1).text())
        self.links.setHosters.connect(self.add_hosters)
        self.links.start()

    @pyqtSlot(str)
    def filter_table(self, text: str) -> None:
        valid_rows = []
        if len(text) > 0:
            for item in self.table.findItems(text, Qt.MatchContains):
                valid_rows.append(item.row())
        for row in range(0, self.table.rowCount()):
            if len(text) > 0 and row not in valid_rows:
                self.table.hideRow(row)
            else:
                self.table.showRow(row)

    @pyqtSlot(bool)
    def aria2_confirmation(self, success: bool) -> None:
        if success:
            message = QMessageBox.information(self, 'Aria2 RPC Daemon',
                                              'Download link has been successfully queued',
                                              QMessageBox.Ok)
        else:
            message = QMessageBox.critical(self, 'Aria2 RPC Daemon',
                                              'Could not queue download link with the Aria2 RPC Daemon. Check your settings in tvlinker.ini',
                                              QMessageBox.Ok)

    @pyqtSlot(str)
    def download_link(self, link: str) -> None:
        if len(self.realdebrid_api_token) > 0:
            link = self.unrestrict_link(link)
        if self.download_manager == 'aria2':
            self.aria2 = Aria2Thread(settings=self.settings, link_url=link)
            self.aria2.aria2Confirmation.connect(self.aria2_confirmation)
            self.aria2.start()
        elif self.download_manager == 'pyload':
            self.pyload_conn = PyloadConnection(config=self.pyload_config)
            pid = self.pyload_conn.addPackage(name='TVLinker', links=[link])
            message = QMessageBox.information(self, 'pyload Download Manager',
                                              'Download link has been successfully queued',
                                              QMessageBox.Ok)
            open_pyload = message.addButton('Open pyLoad', QMessageBox.AcceptRole)
            open_pyload.clicked.connect(self.open_pyload)
        elif self.download_manager == 'idm':
            import os, shlex, subprocess
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            cmd = '"%s" /n /d "%s"' % (self.idm_install_path, link)
            proc = subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE, startupinfo=si, env=os.environ, shell=False)
            proc.wait()
            message = QMessageBox.information(self, 'Internet Download Manager',
                                              'Download link has been successfully queued in IDM',
                                              QMessageBox.Ok)
        else:
            pass
        self.hosters_win.hide()

    def open_pyload(self):
        QDesktopServices.openUrl(QUrl(self.pyload_config.host))

    @pyqtSlot(str)
    def copy_download_link(self, link: str) -> None:
        if len(self.realdebrid_api_token) > 0:
            link = self.unrestrict_link(link)
        clip = qApp.clipboard()
        clip.setText(link)
        self.hosters_win.hide()

    def unrestrict_link(self, link: str) -> str:
        conn = http.client.HTTPSConnection('api.real-debrid.com')
        payload = 'link=%s' % quote_plus(link)
        headers = {
            'Authorization': 'Bearer %s' % self.realdebrid_api_token,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache'
        }
        conn.request('POST', '/rest/1.0/unrestrict/link', payload, headers)
        res = conn.getresponse()
        data = res.read()
        jsondoc = QJsonDocument.fromJson(data)
        if jsondoc.isObject():
            api_result = jsondoc.object()
            if 'download' in api_result.keys():
                dl_link = api_result['download'].toString()
                return dl_link

    @staticmethod
    def get_path(path: str = None, override: bool = False) -> str:
        if override:
            return os.path.join(QFileInfo(__file__).absolutePath(), path)
        return ':assets/%s' % path

    def closeEvent(self, event: QCloseEvent) -> None:
        self.table.deleteLater()
        self.deleteLater()
        qApp.quit()


def main():
    import sys
    app = QApplication(sys.argv)
    app.setOrganizationName('ozmartians.com')
    app.setApplicationName('TVLinker')
    app.setQuitOnLastWindowClosed(True)
    tv = TVLinker()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
