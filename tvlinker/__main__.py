#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import os
import platform
import re
import sys
import warnings
from datetime import datetime
from enum import Enum
from signal import SIGINT, SIGTERM, SIG_DFL, signal

from PyQt5.QtCore import (QFile, QFileInfo, QModelIndex, QProcess, QSettings, QSize, QStandardPaths, QTextStream, QUrl,
                          Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QCloseEvent, QDesktopServices, QFont, QFontDatabase, QIcon, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QApplication, QComboBox, QFileDialog, QGroupBox,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu, QMessageBox, QProgressBar, QPushButton,
                             QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, qApp)

from tvlinker.direct_download import DirectDownload
from tvlinker.hosters import HosterLinks
from tvlinker.pyload import PyloadConnection
from tvlinker.settings import Settings
from tvlinker.threads import (Aria2Thread, DownloadThread, HostersThread, RealDebridAction, RealDebridThread,
                              ScrapeThread)
import tvlinker.assets

if sys.platform == 'win32':
    from PyQt5.QtWinExtras import QWinTaskbarButton


if sys.platform.startswith('linux'):
    import tvlinker.notify as notify

signal(SIGINT, SIG_DFL)
signal(SIGTERM, SIG_DFL)
warnings.filterwarnings('ignore')


class TVLinker(QWidget):
    errorSignal = pyqtSignal()

    def __init__(self, settings: QSettings, parent=None):
        super(TVLinker, self).__init__(parent)
        self.rows, self.cols = 0, 0
        self.parent = parent
        self.settings = settings
        self.proc = None
        self.init_styles()
        self.init_settings()
        self.init_icons()
        if sys.platform.startswith('linux'):
            notify.init(qApp.applicationName())
        layout = QVBoxLayout(spacing=0)
        layout.setContentsMargins(10, 10, 10, 0)
        form_groupbox = QGroupBox(self, objectName='mainForm')
        form_groupbox.setLayout(self.init_form())
        layout.addWidget(form_groupbox)
        layout.addWidget(self.init_table())
        layout.addLayout(self.init_metabar())
        self.setLayout(layout)
        self.setWindowTitle(qApp.applicationName())
        qApp.setWindowIcon(self.icon_app)
        self.resize(FixedSettings.windowSize)
        self.show()
        self.start_scraping()

    @staticmethod
    def load_stylesheet(qssfile: str) -> None:
        if QFileInfo(qssfile).exists():
            qss = QFile(qssfile)
            qss.open(QFile.ReadOnly | QFile.Text)
            qApp.setStyleSheet(QTextStream(qss).readAll())

    def init_styles(self) -> None:
        if sys.platform == 'darwin':
            qss_stylesheet = self.get_path('%s_osx.qss' % qApp.applicationName().lower())
        else:
            qss_stylesheet = self.get_path('%s.qss' % qApp.applicationName().lower())
        self.load_stylesheet(qss_stylesheet)
        QFontDatabase.addApplicationFont(':assets/fonts/opensans.ttf')
        QFontDatabase.addApplicationFont(':assets/fonts/opensans-bold.ttf')
        QFontDatabase.addApplicationFont(':assets/fonts/opensans-semibold.ttf')
        qApp.setFont(QFont('Open Sans', 12 if sys.platform == 'darwin' else 10))

    def init_icons(self) -> None:
        self.icon_app = QIcon(self.get_path('images/%s.png' % qApp.applicationName().lower()))
        self.icon_faves_off = QIcon(':assets/images/star_off.png')
        self.icon_faves_on = QIcon(':assets/images/star_on.png')
        self.icon_refresh = QIcon(':assets/images/refresh.png')
        self.icon_menu = QIcon(':assets/images/menu.png')
        self.icon_settings = QIcon(':assets/images/cog.png')
        self.icon_updates = QIcon(':assets/images/cloud.png')

    def init_settings(self) -> None:
        self.source_url = self.settings.value('source_url')
        self.user_agent = self.settings.value('user_agent')
        self.updater_freq = self.settings.value('updater_freq')
        self.updater_lastcheck = self.settings.value('updater_lastcheck')
        self.dl_pagecount = int(self.settings.value('dl_pagecount', 20))
        self.dl_pagelinks = FixedSettings.linksPerPage
        self.realdebrid_api_token = self.settings.value('realdebrid_apitoken')
        self.download_manager = self.settings.value('download_manager')
        self.persepolis_cmd = self.settings.value('persepolis_cmd')
        self.pyload_host = self.settings.value('pyload_host')
        self.pyload_username = self.settings.value('pyload_username')
        self.pyload_password = self.settings.value('pyload_password')
        self.idm_exe_path = self.settings.value('idm_exe_path')
        self.kget_cmd = self.settings.value('kget_cmd')
        self.favorites = self.settings.value('favorites')

    def init_form(self) -> QHBoxLayout:
        self.search_field = QLineEdit(self, clearButtonEnabled=True, placeholderText='Enter search criteria')
        self.search_field.setObjectName('searchInput')
        self.search_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_field.setFocus()
        self.search_field.textChanged.connect(self.clear_filters)
        self.search_field.returnPressed.connect(lambda: self.filter_table(self.search_field.text()))
        self.favorites_button = QPushButton(parent=self, flat=True, cursor=Qt.PointingHandCursor,
                                            objectName='favesButton', toolTip='Favorites', checkable=True,
                                            toggled=self.filter_faves)
        self.refresh_button = QPushButton(parent=self, flat=True, cursor=Qt.PointingHandCursor,
                                          objectName='refreshButton', toolTip='Refresh', clicked=self.start_scraping)
        self.dlpages_field = QComboBox(self, toolTip='Pages', editable=False, cursor=Qt.PointingHandCursor)
        self.dlpages_field.addItems(('10', '20', '30', '40', '50'))
        self.dlpages_field.setCurrentIndex(self.dlpages_field.findText(str(self.dl_pagecount), Qt.MatchFixedString))
        self.dlpages_field.currentIndexChanged.connect(self.update_pagecount)
        self.settings_button = QPushButton(parent=self, flat=True, toolTip='Menu',
                                           objectName='menuButton', cursor=Qt.PointingHandCursor)
        self.settings_button.setMenu(self.settings_menu())
        layout = QHBoxLayout(spacing=10)
        logo = QPixmap(self.get_path('images/tvrelease.png'))
        layout.addWidget(QLabel(pixmap=logo.scaledToHeight(36, Qt.SmoothTransformation)))
        layout.addWidget(self.search_field)
        layout.addWidget(self.favorites_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(QLabel('Pages:'))
        layout.addWidget(self.dlpages_field)
        layout.addWidget(self.settings_button)
        return layout

    def settings_menu(self) -> QMenu:
        settings_action = QAction(self.icon_settings, 'Settings', self, triggered=self.show_settings)
        updates_action = QAction(self.icon_updates, 'Check for updates', self, triggered=self.check_update)
        aboutqt_action = QAction('About Qt', self, triggered=qApp.aboutQt)
        about_action = QAction('About %s' % qApp.applicationName(), self, triggered=self.about_app)
        menu = QMenu()
        menu.addAction(settings_action)
        menu.addAction(updates_action)
        menu.addSeparator()
        menu.addAction(aboutqt_action)
        menu.addAction(about_action)
        return menu

    def init_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 4, self)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.hideColumn(1)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setHorizontalHeaderLabels(('DATE', 'URL', 'DESCRIPTION', 'FORMAT'))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(100)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.sortByColumn(0, Qt.DescendingOrder)
        self.table.doubleClicked.connect(self.show_hosters)
        return self.table

    def init_metabar(self) -> QHBoxLayout:
        self.meta_template = 'Total number of links retrieved: <b>%i</b> / <b>%i</b>'
        self.progress = QProgressBar(parent=self, minimum=0, maximum=(self.dl_pagecount * self.dl_pagelinks),
                                     visible=False)
        if sys.platform == 'win32':
            self.win_taskbar_button = QWinTaskbarButton(self)

        self.meta_label = QLabel(textFormat=Qt.RichText, alignment=Qt.AlignRight, objectName='totals')
        self.update_metabar()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 10)
        layout.addWidget(self.progress, Qt.AlignLeft)
        layout.addWidget(self.meta_label, Qt.AlignRight)
        return layout

    def init_win_taskbar_progress(self):
        self.win_taskbar_button.setWindow(self.windowHandle())
        # self.win_taskbar_button.setOverlayIcon()
        self.win_taskbar_progress = self.win_taskbar_button.progress()
        self.win_taskbar_progress.setRange(0, self.dl_pagecount * self.dl_pagelinks)
        # self.win_taskbar_progress.setVisible(False)

    @pyqtSlot()
    def check_update(self) -> None:
        QDesktopServices.openUrl(QUrl(FixedSettings.latest_release_url))

    @pyqtSlot()
    def show_settings(self) -> None:
        settings_win = Settings(self, self.settings)
        settings_win.exec_()

    def update_metabar(self) -> bool:
        rowcount = self.table.rowCount()
        self.meta_label.setText(self.meta_template % (rowcount, self.dl_pagecount * self.dl_pagelinks))
        self.progress.setValue(rowcount)
        if sys.platform == 'win32':
            self.win_taskbar_button.progress().setValue(self.progress.value())
        return True

    def start_scraping(self) -> None:
        self.rows = 0
        if self.table.rowCount() > 0:
            self.table.clearContents()
            self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        self.scrape = ScrapeThread(settings=self.settings, maxpages=self.dl_pagecount)
        self.scrape.addRow.connect(self.add_row)
        self.scrape.started.connect(self.show_progress)
        self.scrape.finished.connect(self.scrape_finished)
        self.progress.setValue(0)
        self.scrape.start()

    @pyqtSlot()
    def about_app(self) -> None:
        about_html = '''<style>
        a { color:#441d4e; text-decoration:none; font-weight:bold; }
        a:hover { text-decoration:underline; }
    </style>
    <p style="font-size:24pt; font-weight:bold; color:#6A687D;">%s</p>
    <p>
        <span style="font-size:13pt;"><b>Version: %s</b></span>
        <span style="font-size:10pt;position:relative;left:5px;">( %s )</span>
    </p>
    <p style="font-size:13px;">
        Copyright &copy; %s <a href="mailto:pete@ozmartians.com">Pete Alexandrou</a>
        <br/>
        Web: <a href="%s">%s</a>
    </p>
    <p style="font-size:11px;">
        This program is free software; you can redistribute it and/or
        modify it under the terms of the GNU General Public License
        as published by the Free Software Foundation; either version 2
        of the License, or (at your option) any later version.
    </p>''' % (qApp.applicationName(), qApp.applicationVersion(), platform.architecture()[0],
               datetime.now().year, qApp.organizationDomain(), qApp.organizationDomain())
        QMessageBox.about(self, 'About %s' % qApp.applicationName(), about_html)

    @pyqtSlot(int)
    def update_pagecount(self, index: int) -> None:
        self.dl_pagecount = int(self.dlpages_field.itemText(index))
        self.progress.setMaximum(self.dl_pagecount * self.dl_pagelinks)
        if sys.platform == 'win32':
            self.win_taskbar_button.progress().setMaximum(self.dl_pagecount * self.dl_pagelinks)
        self.start_scraping()

    @pyqtSlot()
    def show_progress(self):
        self.progress.show()
        if sys.platform == 'win32':
            self.win_taskbar_button.setWindow(self.windowHandle())
            self.win_taskbar_button.progress().setRange(0, self.dl_pagecount * self.dl_pagelinks)
            self.win_taskbar_button.progress().setVisible(True)
            self.win_taskbar_button.progress().setValue(self.progress.value())

    @pyqtSlot()
    def scrape_finished(self) -> None:
        self.progress.hide()
        if sys.platform == 'win32':
            self.win_taskbar_button.progress().setVisible(False)
        self.table.setSortingEnabled(True)
        self.filter_table(text='')

    @pyqtSlot(list)
    def add_row(self, row: list) -> None:
        self.cols = 0
        self.table.setRowCount(self.rows + 1)
        if self.table.cursor() != Qt.PointingHandCursor:
            self.table.setCursor(Qt.PointingHandCursor)
        for item in row:
            table_item = QTableWidgetItem(item)
            table_item.setToolTip('%s\n\nDouble-click to view hoster links.' % row[1])
            table_item.setFont(QFont('Open Sans', weight=QFont.Normal))
            if self.cols == 2:
                if sys.platform == 'win32':
                    table_item.setFont(QFont('Open Sans Semibold', pointSize=10))
                elif sys.platform == 'darwin':
                    table_item.setFont(QFont('Open Sans Bold', weight=QFont.Bold))
                else:
                    table_item.setFont(QFont('Open Sans', weight=QFont.DemiBold, pointSize=10))
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
    def show_hosters(self, index: QModelIndex) -> None:
        qApp.setOverrideCursor(Qt.BusyCursor)
        self.hosters_win = HosterLinks(parent=self, title=self.table.item(self.table.currentRow(), 2).text())
        self.hosters_win.downloadLink.connect(self.download_link)
        self.hosters_win.copyLink.connect(self.copy_download_link)
        self.links = HostersThread(settings=self.settings, link_url=self.table.item(self.table.currentRow(), 1).text())
        self.links.setHosters.connect(self.add_hosters)
        self.links.start()

    @pyqtSlot(bool)
    def filter_faves(self, checked: bool) -> None:
        if self.scrape.isFinished():
            self.filter_table(text='')

    @pyqtSlot(str)
    def filter_table(self, text: str) -> None:
        filters = []
        if self.favorites_button.isChecked():
            filters = self.favorites
        if len(text):
            filters.append(text)
        if not len(filters) or not hasattr(self, 'valid_rows'):
            self.valid_rows = []
        for search_term in filters:
            for item in self.table.findItems(search_term, Qt.MatchContains):
                self.valid_rows.append(item.row())
        for row in range(0, self.table.rowCount()):
            if not len(filters):
                self.table.showRow(row)
            else:
                if row not in self.valid_rows:
                    self.table.hideRow(row)
                else:
                    self.table.showRow(row)

    @pyqtSlot()
    def clear_filters(self):
        if not len(self.search_field.text()):
            self.filter_table('')

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
            self.unrestrict_link(link, True)
        else:
            if self.download_manager == 'aria2':
                self.aria2 = Aria2Thread(settings=self.settings, link_url=link)
                self.aria2.aria2Confirmation.connect(self.aria2_confirmation)
                self.aria2.start()
                self.hosters_win.close()
            elif self.download_manager == 'pyload':
                self.pyload_conn = PyloadConnection(self.pyload_host, self.pyload_username, self.pyload_password)
                pid = self.pyload_conn.addPackage(name='TVLinker', links=[link])
                qApp.restoreOverrideCursor()
                self.hosters_win.close()
                msgbox = QMessageBox.information(self, 'pyLoad Download Manager',
                                                 'Download link has been successfully queued in pyLoad.',
                                                 QMessageBox.Ok)
                open_pyload = msgbox.addButton('Open pyLoad', QMessageBox.AcceptRole)
                open_pyload.clicked.connect(self.open_pyload)
            elif self.download_manager in ('kget', 'persepolis'):
                provider = self.kget_cmd if self.download_manager == 'kget' else self.persepolis_cmd
                cmd = '{0} "{1}"'.format(provider, link)
                if self.cmdexec(cmd):
                    qApp.restoreOverrideCursor()
                    self.hosters_win.close()
                    if sys.platform.startswith('linux'):
                        self.notify(title='Download added to %s' % self.download_manager, icon='success')
                    else:
                        QMessageBox.information(self, self.download_manager, 'Your link has been queued in %s.'
                                                % self.download_manager, QMessageBox.Ok)
            elif self.download_manager == 'idm':
                cmd = '"%s" /n /d "%s"' % (self.idm_exe_path, link)
                if self.cmdexec(cmd):
                    qApp.restoreOverrideCursor()
                    self.hosters_win.close()
                    QMessageBox.information(self, 'Internet Download Manager', 'Your link has been queued in IDM.',
                                            QMessageBox.Ok)
                else:
                    print('IDM QProcess error = %s' % ProcError(self.idm.error()).name)
                    qApp.restoreOverrideCursor()
                    self.hosters_win.close()
                    QMessageBox.critical(self, 'Internet Download Manager',
                                         '<p>Could not connect to your local IDM application instance. ' +
                                         'Please check your settings and ensure the IDM executable path is correct ' +
                                         'according to your installation.</p><p>Error Code: %s</p>'
                                         % ProcError(self.idm.error()).name, QMessageBox.Ok)
            else:
                dlpath, _ = QFileDialog.getSaveFileName(self, 'Save File', link.split('/')[-1])
                if dlpath != '':
                    self.directdl_win = DirectDownload(parent=self)
                    self.directdl = DownloadThread(link_url=link, dl_path=dlpath)
                    self.directdl.dlComplete.connect(self.directdl_win.download_complete)
                    self.directdl.dlProgressTxt.connect(self.directdl_win.update_progress_label)
                    self.directdl.dlProgress.connect(self.directdl_win.update_progress)
                    self.directdl_win.cancelDownload.connect(self.cancel_download)
                    self.directdl.start()
                    self.hosters_win.close()

    def notify(self, title: str, msg: str = '', icon: str = None, urgency: int = 1) -> bool:
        if icon is None:
            icon = self.get_path('assets/images/tvlinker.png', override=True)
        elif icon == 'success':
            icon = self.get_path('assets/images/thumbsup.png', override=True)
        notification = notify.Notification(title, msg, icon)
        notification.set_urgency(urgency)
        return notification.show()

    def cmdexec(self, cmd: str) -> bool:
        if self.proc is None:
            self.proc = QProcess()
            self.proc.setProcessChannelMode(QProcess.MergedChannels)
        if hasattr(self.proc, 'errorOccurred'):
            self.proc.errorOccurred.connect(lambda error: print('Process error = %s' % ProcError(error).name))
        if self.proc.state() == QProcess.NotRunning:
            self.proc.start(cmd)
            self.proc.waitForFinished(-1)
            self.proc.deleteLater()
            return self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0
        return False

    @pyqtSlot()
    def cancel_download(self) -> None:
        self.directdl.cancel_download = True
        self.directdl.terminate()
        self.directdl.deleteLater()

    def open_pyload(self) -> None:
        QDesktopServices.openUrl(QUrl(self.pyload_config.host))

    @pyqtSlot(str)
    def copy_download_link(self, link: str) -> None:
        if len(self.realdebrid_api_token) > 0 and 'real-debrid.com' not in link:
            qApp.setOverrideCursor(Qt.BusyCursor)
            self.unrestrict_link(link, False)
        else:
            clip = qApp.clipboard()
            clip.setText(link)
            self.hosters_win.close()
            qApp.restoreOverrideCursor()

    def unrestrict_link(self, link: str, download: bool = True) -> None:
        caller = inspect.stack()[1].function
        self.realdebrid = RealDebridThread(settings=self.settings, api_url=FixedSettings.realdebrid_api_url,
                                           link_url=link, action=RealDebridAction.UNRESTRICT_LINK)
        if download:
            self.realdebrid.unrestrictedLink.connect(self.download_link)
        else:
            self.realdebrid.unrestrictedLink.connect(self.copy_download_link)
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


class ProcError(Enum):
    FAILED_TO_START = 0
    CRASHED = 1
    TIMED_OUT = 2
    READ_ERROR = 3
    WRITE_ERROR = 4
    UNKNOWN_ERROR = 5


class FixedSettings:
    applicationName = 'TVLinker'
    applicationVersion = TVLinker.get_version()
    organizationDomain = 'http://tvlinker.ozmartians.com'
    windowSize = QSize(1000, 785)
    linksPerPage = 20
    latest_release_url = 'https://github.com/ozmartian/tvlinker/releases/latest'
    realdebrid_api_url = 'https://api.real-debrid.com/rest/1.0'

    @staticmethod
    def get_app_settings() -> QSettings:
        config_path = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        settings_ini = os.path.join(config_path, '%s.ini' % FixedSettings.applicationName.lower())
        if not os.path.exists(settings_ini):
            os.makedirs(config_path, exist_ok=True)
            QFile.copy(':%s.ini' % FixedSettings.applicationName.lower(), settings_ini)
            if os.name == 'posix':
                QFile.setPermissions(settings_ini, QFile.ReadOwner | QFile.WriteOwner)
        return QSettings(settings_ini, QSettings.IniFormat)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(FixedSettings.applicationName)
    app.setOrganizationDomain(FixedSettings.organizationDomain)
    app.setApplicationVersion(FixedSettings.applicationVersion)
    app.setQuitOnLastWindowClosed(True)
    app.setAttribute(Qt.AA_NativeWindows, True)
    tvlinker = TVLinker(FixedSettings.get_app_settings())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
