#!/usr/bin/env pyton3
# -*- coding: utf-8 -*-

import inspect
import os
import platform
import re
import signal
import sys

from PyQt5.QtCore import (QFile, QFileInfo, QJsonDocument, QModelIndex, QSettings,
                          QSize, QStandardPaths, Qt, QTextStream, QUrl, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QCloseEvent, QColor, QDesktopServices,
                         QFont, QFontDatabase, QIcon, QPalette, QPixmap)
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QApplication,
                             QComboBox, QDialog, QFileDialog, QHBoxLayout,
                             QHeaderView, QLabel, QLayout, QLineEdit, QMenu,
                             QMessageBox, QProgressBar, QPushButton,
                             QSizePolicy, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, qApp)
from hosters import HosterLinks
from pyload import PyloadConnection, PyloadConfig
from settings import Settings
from threads import (HostersThread, ScrapeThread, RealDebridThread,
                    Aria2Thread, DownloadThread)
import assets

signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)


class DirectDownload(QDialog):

    cancelDownload = pyqtSignal()

    def __init__(self, parent, f=Qt.WindowCloseButtonHint):
        super(DirectDownload, self).__init__(parent, f)
        self.parent = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(485)
        self.setContentsMargins(20, 20, 20, 20)
        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.progress_label = QLabel(alignment=Qt.AlignCenter)
        self.progress = QProgressBar(self.parent, minimum=0, maximum=100)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress)
        self.setLayout(layout)
        self.setWindowTitle('Download Progress')

    def closeEvent(self, event: QCloseEvent) -> None:
        qApp.restoreOverrideCursor()
        self.cancelDownload.emit()
        super(DirectDownload, self).closeEvent(event)

    @pyqtSlot(int)
    def update_progress(self, progress: int) -> None:
        self.progress.setValue(progress)

    @pyqtSlot(str)
    def update_progress_label(self, progress_txt: str) -> None:
        if self.isHidden():
            self.show()
        self.progress_label.setText(progress_txt)

    @pyqtSlot()
    def download_complete(self) -> None:
        qApp.restoreOverrideCursor()
        QMessageBox.information(self.parent, 'Confirmation', 'The download is complete...                    ',
                                buttons=QMessageBox.Ok)
        self.close()


class TVLinker(QWidget):
    def __init__(self):
        super(TVLinker, self).__init__()
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
        self.resize(FixedSettings.windowSize)
        self.show()
        self.start_scraping()

    def init_stylesheet(self) -> None:
        qss_stylesheet = '%s.qss' % qApp.applicationName().lower()
        if sys.platform == 'win32':
            qss_stylesheet = '%s_win32.qss' % qApp.applicationName().lower()
        QFontDatabase.addApplicationFont(self.get_path('fonts/OpenSans.ttf'))
        qss = QFile(':assets/%s' % qss_stylesheet)
        qss.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(qss)
        qApp.setStyleSheet(stream.readAll())

    def init_settings(self) -> None:
        self.config_path = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        self.settings_ini = os.path.join(self.config_path, '%s.ini' % qApp.applicationName().lower())
        if not os.path.exists(self.settings_ini):
            os.makedirs(self.config_path, exist_ok=True)
            QFile.copy(self.get_path(path='%s.ini' % qApp.applicationName().lower(), override=True), self.settings_ini)
        self.settings_ini_secret = os.path.join(self.config_path, '%s.ini.secret' % qApp.applicationName().lower())
        self.settings_path = self.settings_ini_secret if os.path.exists(self.settings_ini_secret) else self.settings_ini
        self.settings = QSettings(self.settings_path, QSettings.IniFormat)
        self.source_url = self.settings.value('source_url')
        self.user_agent = self.settings.value('user_agent')
        self.dl_pagecount = int(self.settings.value('dl_pagecount'))
        self.dl_pagelinks = FixedSettings.linksPerPage
        self.realdebrid_api_token = self.settings.value('realdebrid_apitoken')
        self.download_manager = self.settings.value('download_manager')
        if self.download_manager == 'pyLoad':
            self.pyload_config = PyloadConfig()
            self.pyload_config.host = self.settings.value('pyload_host')
            self.pyload_config.username = self.settings.value('pyload_username')
            self.pyload_config.password = self.settings.value('pyload_password')
        elif self.download_manager == 'IDM':
            self.idm_exe_path = self.settings.value('idm_exe_path')

    def init_form(self) -> QHBoxLayout:
        logo = QPixmap(self.get_path('images/tvrelease.png'))
        self.search_field = QLineEdit(self, clearButtonEnabled=True, placeholderText='Enter search criteria')
        self.search_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_field.setFocus()
        self.search_field.textChanged.connect(self.filter_table)
        self.dlpages_field = QComboBox(self, toolTip='Pages', editable=False, cursor=Qt.PointingHandCursor)
        self.dlpages_field.addItems(('10', '20', '30', '40', '50'))
        self.dlpages_field.setCurrentIndex(self.dlpages_field.findText(str(self.dl_pagecount), Qt.MatchFixedString))
        self.dlpages_field.currentIndexChanged.connect(self.update_pagecount)
        self.refresh_button = QPushButton(parent=self, flat=False, text='Refresh', cursor=Qt.PointingHandCursor,
                                          toolTip='Refresh', icon=QIcon(self.get_path('images/refresh.png')),
                                          clicked=self.refresh_links)
        menu_icon = QPixmap(self.get_path('images/menu.png'))
        self.settings_button = QPushButton(parent=self, flat=True, toolTip='Menu', cursor=Qt.PointingHandCursor,
                                            icon=QIcon(menu_icon))
        self.settings_button.setMenu(self.settings_menu())
        layout = QHBoxLayout()
        layout.addWidget(QLabel(pixmap=logo.scaledToHeight(36, Qt.SmoothTransformation)))
        layout.addWidget(self.search_field)
        layout.addWidget(QLabel('Pages:'))
        layout.addWidget(self.dlpages_field)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.settings_button)
        return layout

    def settings_menu(self) -> QMenu:
        settings_action = QAction(QIcon(self.get_path('images/settings.png')), 'Configure %s...' % qApp.applicationName(),
                                  self, triggered=self.show_settings)
        aboutQt_action = QAction(QIcon(self.get_path('images/qt.png')), 'About Qt', self, triggered=qApp.aboutQt)
        about_action = QAction(QIcon(self.get_path('images/tvlinker.png')), 'About %s' % qApp.applicationName(),
                                  self, triggered=self.about_app)
        menu = QMenu()
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(aboutQt_action)
        menu.addAction(about_action)
        return menu

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
        self.meta_template = 'Total number of links retrieved: <b>%s</b>'
        self.progress = QProgressBar(parent=self, minimum=0, maximum=(self.dl_pagecount * self.dl_pagelinks),
                                     visible=False)
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
        settings_win = Settings(self, self.settings)
        settings_win.exec_()

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

    @pyqtSlot()
    def about_app(self) -> None:
        about_html = '''<style>
        a { color:#441d4e; text-decoration:none; font-weight:bold; }
        a:hover { text-decoration:underline; }
    </style>
    <p style="font-size:26pt; font-weight:bold;">%s</p>
    <p>
        <span style="font-size:13pt;"><b>Version: %s</b></span>
        <span style="font-size:10pt;position:relative;left:5px;">( %s )</span>
    </p>
    <p style="font-size:13px;">
        Copyright &copy; 2016 <a href="mailto:pete@ozmartians.com">Pete Alexandrou</a>
        <br/>
        Web: <a href="%s">%s</a>
    </p>
    <p style="font-size:11px;">
        This program is free software; you can redistribute it and/or
        modify it under the terms of the GNU General Public License
        as published by the Free Software Foundation; either version 2
        of the License, or (at your option) any later version.
    </p>''' % (qApp.applicationName(), qApp.applicationVersion(), platform.architecture()[0],
               qApp.organizationDomain(), qApp.organizationDomain())
        QMessageBox.about(self, 'About %s' % qApp.applicationName(), about_html)

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
            table_item.setToolTip('%s\n\nDouble-click to view hoster links.' % row[1])
            table_item.setFont(QFont('Open Sans', weight=QFont.Normal))
            if self.cols == 2:
                table_item.setFont(QFont('Open Sans', weight=QFont.DemiBold))
                table_item.setText('  ' + table_item.text())
            elif self.cols in (0, 3):
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
        self.hosters_win = HosterLinks(parent=self, title=self.table.item(self.table.currentRow(), 2).text())
        self.hosters_win.downloadLink.connect(self.download_link)
        self.hosters_win.copyLink.connect(self.copy_download_link)
        self.hosters_win.show()
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
        qApp.restoreOverrideCursor()
        if success:
            QMessageBox.information(self, 'Aria2 RPC Daemon',
                                    'Download link has been successfully queued in Aria2.', QMessageBox.Ok)
        else:
            QMessageBox.critical(self, 'Aria2 RPC Daemon',
                                 'Could not connect to Aria2 RPC Daemon. ' +
                                 'Check your %s settings and try again.' % qApp.applicationName(), QMessageBox.Ok)

    @pyqtSlot(str)
    def download_link(self, link: str) -> None:
        if len(self.realdebrid_api_token) > 0 and 'real-debrid.com' not in link:
            qApp.setOverrideCursor(Qt.BusyCursor)
            link = self.unrestrict_link(link)
        else:
            if self.download_manager == 'aria2':
                self.aria2 = Aria2Thread(settings=self.settings, link_url=link)
                self.aria2.aria2Confirmation.connect(self.aria2_confirmation)
                self.aria2.start()
                self.hosters_win.close()
            elif self.download_manager == 'pyLoad':
                self.pyload_conn = PyloadConnection(config=self.pyload_config)
                pid = self.pyload_conn.addPackage(name='TVLinker', links=[link])
                qApp.restoreOverrideCursor()
                self.hosters_win.close()
                msgbox = QMessageBox.information(self, 'pyLoad Download Manager',
                                                 'Download link has been successfully queued in pyLoad.', QMessageBox.Ok)
                open_pyload = msgbox.addButton('Open pyLoad', QMessageBox.AcceptRole)
                open_pyload.clicked.connect(self.open_pyload)
            elif self.download_manager == 'IDM':
                import shlex, subprocess
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                cmd = '"%s" /n /d "%s"' % (self.idm_exe_path, link)
                proc = subprocess.Popen(args=shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        stdin=subprocess.PIPE, startupinfo=si, env=os.environ, shell=False)
                proc.wait()
                qApp.restoreOverrideCursor()
                self.hosters_win.close()
                QMessageBox.information(self, 'Internet Download Manager',
                                        'Your link has been queued in IDM.', QMessageBox.Ok)
            else:
                dlpath, _ = QFileDialog.getSaveFileName(self, 'Save File', link.split('/')[-1])
                if dlpath == '':
                    return
                self.directdl_win = DirectDownload(parent=self)
                self.directdl = DownloadThread(link_url=link, dl_path=dlpath)
                self.directdl.dlComplete.connect(self.directdl_win.download_complete)
                self.directdl.dlProgressTxt.connect(self.directdl_win.update_progress_label)
                self.directdl.dlProgress.connect(self.directdl_win.update_progress)
                self.directdl_win.cancelDownload.connect(self.cancel_download)
                self.directdl.start()
                self.hosters_win.close()

    @pyqtSlot()
    def cancel_download(self) -> None:
        self.directdl.cancel_download = True
        self.directdl.terminate()
        self.directdl.deleteLater()

    def open_pyload(self):
        QDesktopServices.openUrl(QUrl(self.pyload_config.host))

    @pyqtSlot(str)
    def copy_download_link(self, link: str) -> None:
        if len(self.realdebrid_api_token) > 0 and 'real-debrid.com' not in link:
            qApp.setOverrideCursor(Qt.BusyCursor)
            link = self.unrestrict_link(link)
        else:
            clip = qApp.clipboard()
            clip.setText(link)
            self.hosters_win.close()
            qApp.restoreOverrideCursor()

    def unrestrict_link(self, link: str) -> None:
        caller = inspect.stack()[1].function
        self.realdebrid = RealDebridThread(settings=self.settings, api_url=FixedSettings.realdebrid_api_url, link_url=link)
        self.realdebrid.unrestrictedLink.connect(getattr(self, caller))
        self.realdebrid.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.table.deleteLater()
        self.deleteLater()
        qApp.quit()

    @staticmethod
    def get_path(path: str = None, override: bool = False) -> str:
        if override:
            if getattr(sys, 'frozen', False):
                return os.path.join(sys._MEIPASS, path)
            return os.path.join(QFileInfo(__file__).absolutePath(), path)
        return ':assets/%s' % path

    @staticmethod
    def get_version(filename: str = '__init__.py') -> str:
        with open(TVLinker.get_path(filename, override=True), 'r') as initfile:
            for line in initfile.readlines():   
                m = re.match('__version__ *= *[\'](.*)[\']', line)
                if m:
                    return m.group(1)


class FixedSettings:
    applicationName = 'TVLinker'
    applicationVersion = TVLinker.get_version()
    applicationStyle = 'Fusion'
    organizationDomain = 'http://tvlinker.ozmartians.com'
    windowSize = QSize(1000, 750)
    linksPerPage = 30
    realdebrid_api_url = 'https://api.real-debrid.com/rest/1.0'


def main():
    if sys.platform == 'win32':
        qApp.setStyle(FixedSettings.applicationStyle)
    app = QApplication(sys.argv)
    app.setApplicationName(FixedSettings.applicationName)
    app.setOrganizationDomain(FixedSettings.organizationDomain)
    app.setApplicationVersion(FixedSettings.applicationVersion)
    app.setQuitOnLastWindowClosed(True)
    linker = TVLinker()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
