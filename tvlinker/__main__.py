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

from PyQt5.QtCore import (QFile, QFileInfo, QModelIndex, QProcess, QSettings, QSize, QStandardPaths, QTextStream,
                          QThread, QUrl, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QCloseEvent, QColor, QDesktopServices, QFont, QFontDatabase, QIcon, QPalette, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QApplication, QComboBox, QFileDialog, QGroupBox,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu, QMessageBox, QProgressBar,
                             QProxyStyle, QPushButton, QSizePolicy, QStyle, QStyleFactory, QStyleHintReturn,
                             QStyleOption, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, qApp)

from tvlinker.direct_download import DirectDownload
from tvlinker.hosters import HosterLinks
from tvlinker.progress import TaskbarProgress
from tvlinker.pyload import PyloadConnection
from tvlinker.settings import Settings
from tvlinker.threads import Aria2Thread, DownloadThread, HostersThread, RealDebridThread, ScrapeWorker
import tvlinker.assets as assets
import sip


if sys.platform == 'win32':
    from PyQt5.QtWinExtras import QWinTaskbarButton

if sys.platform.startswith('linux'):
    import tvlinker.notify as notify

signal(SIGINT, SIG_DFL)
signal(SIGTERM, SIG_DFL)
warnings.filterwarnings('ignore')


class OverrideStyle(QProxyStyle):
    def styleHint(self, hint, option: QStyleOption=0, widget: QWidget=0, returnData: QStyleHintReturn=0) -> int:
        if hint in {QStyle.SH_UnderlineShortcut, QStyle.SH_DialogButtons_DefaultButton}:
            return 0
        return QProxyStyle.styleHint(self, hint, option, widget, returnData)


class TVLinker(QWidget):
    errorSignal = pyqtSignal()

    def __init__(self, settings: QSettings, parent=None):
        super(TVLinker, self).__init__(parent)
        self.rows, self.cols = 0, 0
        self.parent = parent
        self.settings = settings
        self.taskbar = TaskbarProgress(self)
        self.init_styles()
        self.init_settings()
        self.init_icons()
        if sys.platform.startswith('linux'):
            notify.init(qApp.applicationName())
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(15, 15, 15, 0)

        form_groupbox = QGroupBox(self, objectName='mainForm')
        form_groupbox.setLayout(self.init_form())
        layout.addWidget(form_groupbox)
        layout.addWidget(self.init_table())
        layout.addLayout(self.init_metabar())
        self.setLayout(layout)
        qApp.setWindowIcon(self.icon_app)
        self.resize(FixedSettings.windowSize)
        self.show()
        self.start_scraping()

    class ProcError(Enum):
        FAILED_TO_START = 0
        CRASHED = 1
        TIMED_OUT = 2
        READ_ERROR = 3
        WRITE_ERROR = 4
        UNKNOWN_ERROR = 5

    class NotifyIcon(Enum):
        SUCCESS = ':assets/images/tvlinker.png'
        DEFAULT = ':assets/images/tvlinker.png'

    def init_threads(self, threadtype: str = 'scrape') -> None:
        if threadtype == 'scrape':
            if hasattr(self, 'scrapeThread'):
                if not sip.isdeleted(self.scrapeThread) and self.scrapeThread.isRunning():
                    self.scrapeThread.requestInterruption()
            self.scrapeThread = QThread(self)
            self.scrapeWorker = ScrapeWorker(self.source_url, self.user_agent, self.dl_pagecount)
            self.scrapeThread.started.connect(self.show_progress)
            self.scrapeThread.started.connect(self.scrapeWorker.begin)
            self.scrapeWorker.moveToThread(self.scrapeThread)
            self.scrapeWorker.addRow.connect(self.add_row)
            self.scrapeWorker.workFinished.connect(self.scrape_finished)
            self.scrapeWorker.workFinished.connect(self.scrapeWorker.deleteLater, Qt.DirectConnection)
            self.scrapeWorker.workFinished.connect(self.scrapeThread.quit, Qt.DirectConnection)
            self.scrapeThread.finished.connect(self.scrapeThread.deleteLater, Qt.DirectConnection)
        elif threadtype == 'unrestrict':
            pass

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
        TVLinker.load_stylesheet(qss_stylesheet)
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
        self.provider = 'Scene-RLS'
        self.select_provider(0)
        self.user_agent = self.settings.value('user_agent')
        self.dl_pagecount = self.settings.value('dl_pagecount', 20, int)
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
                                            toggled=self.filter_faves,
                                            checked=self.settings.value('faves_filter', False, bool))
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
        # providerCombo = QComboBox(self, toolTip='Provider', editable=False, cursor=Qt.PointingHandCursor)
        # providerCombo.setObjectName('providercombo')
        # providerCombo.addItem(QIcon(':assets/images/provider-scenerls.png'), '')
        # providerCombo.addItem(QIcon(':assets/images/provider-tvrelease.png'), '')
        # providerCombo.setIconSize(QSize(146, 36))
        # providerCombo.setMinimumSize(QSize(160, 40))
        # providerCombo.setStyleSheet('''
        #     QComboBox, QComboBox::drop-down { background-color: transparent; border: none; margin: 5px; }
        #     QComboBox::down-arrow { image: url(:assets/images/down_arrow.png); }
        #     QComboBox QAbstractItemView { selection-background-color: #DDDDE4; }
        # ''')
        # providerCombo.currentIndexChanged.connect(self.select_provider)
        layout.addWidget(QLabel(pixmap=QPixmap(':assets/images/provider-scenerls.png')))
        layout.addWidget(self.search_field)
        layout.addWidget(self.favorites_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(QLabel('Pages:'))
        layout.addWidget(self.dlpages_field)
        layout.addWidget(self.settings_button)
        return layout

    @pyqtSlot(int)
    def select_provider(self, index: int):
        if index == 0:
            self.provider = 'Scene-RLS'
            self.source_url = 'http://scene-rls.net/releases/index.php?p={0}&cat=TV%20Shows'
        elif index == 1:
            self.provider = 'TV-Release'
            self.source_url = 'http://tv-release.pw/?cat=TV'
        self.setWindowTitle('%s :: %s' % (qApp.applicationName(), self.provider))

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
        self.table.setHorizontalHeaderLabels(('DATE', 'URL', 'DESCRIPTION', 'SIZE'))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(100)
        if sys.platform == 'win32':
            self.table.setStyle(QStyleFactory.create('Fusion'))
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.sortByColumn(0, Qt.DescendingOrder)
        self.table.doubleClicked.connect(self.show_hosters)
        return self.table

    def init_metabar(self) -> QHBoxLayout:
        self.meta_template = 'Total number of links retrieved: <b>%i</b> / <b>%i</b>'
        self.progress = QProgressBar(parent=self, minimum=0, maximum=(self.dl_pagecount * self.dl_pagelinks),
                                     visible=False)
        self.taskbar.setProgress(0.0, True)
        if sys.platform == 'win32':
            self.win_taskbar_button = QWinTaskbarButton(self)

        self.meta_label = QLabel(textFormat=Qt.RichText, alignment=Qt.AlignRight, objectName='totals')
        self.update_metabar()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 10)
        layout.addWidget(self.progress, Qt.AlignLeft)
        layout.addWidget(self.meta_label, Qt.AlignRight)
        return layout

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
        self.taskbar.setProgress(rowcount / self.progress.maximum())
        if sys.platform == 'win32':
            self.win_taskbar_button.progress().setValue(self.progress.value())
        return True

    def start_scraping(self) -> None:
        self.init_threads('scrape')
        self.rows = 0
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        self.update_metabar()
        self.scrapeThread.start()

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
        self.scrapeWorker.maxpages = self.dl_pagecount
        self.progress.setMaximum(self.dl_pagecount * self.dl_pagelinks)
        self.settings.setValue('dl_pagecount', self.dl_pagecount)
        if sys.platform == 'win32':
            self.win_taskbar_button.progress().setMaximum(self.dl_pagecount * self.dl_pagelinks)
        self.start_scraping()

    @pyqtSlot()
    def show_progress(self):
        self.progress.show()
        self.taskbar.setProgress(0.0, True)
        if sys.platform == 'win32':
            self.win_taskbar_button.setWindow(self.windowHandle())
            self.win_taskbar_button.progress().setRange(0, self.dl_pagecount * self.dl_pagelinks)
            self.win_taskbar_button.progress().setVisible(True)
            self.win_taskbar_button.progress().setValue(self.progress.value())

    @pyqtSlot()
    def scrape_finished(self) -> None:
        self.progress.hide()
        self.taskbar.setProgress(0.0, False)
        if sys.platform == 'win32':
            self.win_taskbar_button.progress().setVisible(False)
        self.table.setSortingEnabled(True)
        self.filter_table(text='')

    @pyqtSlot(list)
    def add_row(self, row: list) -> None:
        if not self.scrapeThread.isInterruptionRequested():
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
    def add_hosters(self, links: list) -> None:
        self.hosters_win.show_hosters(links)

    @pyqtSlot(QModelIndex)
    def show_hosters(self, index: QModelIndex) -> None:
        qApp.setOverrideCursor(Qt.BusyCursor)
        self.hosters_win = HosterLinks(self)
        self.hosters_win.downloadLink.connect(self.download_link)
        self.hosters_win.copyLink.connect(self.copy_download_link)
        self.links = HostersThread(self.table.item(self.table.currentRow(), 1).text(), self.user_agent)
        self.links.setHosters.connect(self.add_hosters)
        self.links.noLinks.connect(self.no_links)
        self.links.start()

    @pyqtSlot()
    def no_links(self) -> None:
        self.hosters_win.loading_progress.cancel()
        self.hosters_win.close()
        QMessageBox.warning(self, 'No Links Available', 'No links are available yet for the chosen TV show. ' +
                            'This is most likely due to the files still being uploaded. This is normal if the ' +
                            'link was published 30-45 mins ago.\n\nPlease check back again in 10-15 minutes.')

    @pyqtSlot(bool)
    def filter_faves(self, checked: bool) -> None:
        self.settings.setValue('faves_filter', checked)
        if hasattr(self, 'scrapeWorker') and (sip.isdeleted(self.scrapeWorker) or self.scrapeWorker.complete):
            self.filter_table(text='')

    @pyqtSlot(str)
    def filter_table(self, text: str) -> None:
        filters = []
        if self.favorites_button.isChecked():
            filters = self.favorites
            self.table.sortItems(2, Qt.AscendingOrder)
        else:
            self.table.sortItems(0,Qt.DescendingOrder)
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
            if sys.platform.startswith('linux'):
                self.notify(title=qApp.applicationName(), msg='Your download link has been unrestricted and now ' +
                                                          'queued in Aria2 RPC Daemon', icon=self.NotifyIcon.SUCCESS)
            else:
                QMessageBox.information(self, qApp.applicationName(),
                                        'Download link has been queued in Aria2.', QMessageBox.Ok)
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
                if sys.platform.startswith('linux'):
                    self.notify(title='Download added to %s' % self.download_manager, icon=self.NotifyIcon.SUCCESS)
                else:
                    QMessageBox.information(self, self.download_manager, 'Your link has been queued in %s.'
                                            % self.download_manager, QMessageBox.Ok)
                # open_pyload = msgbox.addButton('Open pyLoad', QMessageBox.AcceptRole)
                # open_pyload.clicked.connect(self.open_pyload)
            elif self.download_manager in ('kget', 'persepolis'):
                provider = self.kget_cmd if self.download_manager == 'kget' else self.persepolis_cmd
                cmd = '{0} "{1}"'.format(provider, link)
                if self.cmdexec(cmd):
                    qApp.restoreOverrideCursor()
                    self.hosters_win.close()
                    if sys.platform.startswith('linux'):
                        self.notify(title='Download added to %s' % self.download_manager, icon=self.NotifyIcon.SUCCESS)
                    else:
                        QMessageBox.information(self, self.download_manager, 'Your link has been queued in %s.'
                                                % self.download_manager, QMessageBox.Ok)
            elif self.download_manager == 'idm':
                cmd = '"%s" /n /d "%s"' % (self.idm_exe_path, link)
                if self.cmdexec(cmd):
                    qApp.restoreOverrideCursor()
                    self.hosters_win.close()
                    QMessageBox.information(self, 'Internet Download Manager', 'Your link has been queued in IDM.')
                else:
                    print('IDM QProcess error = %s' % self.ProcError(self.idm.error()).name)
                    qApp.restoreOverrideCursor()
                    self.hosters_win.close()
                    QMessageBox.critical(self, 'Internet Download Manager',
                                         '<p>Could not connect to your local IDM application instance. ' +
                                         'Please check your settings and ensure the IDM executable path is correct ' +
                                         'according to your installation.</p><p>Error Code: %s</p>'
                                         % self.ProcError(self.idm.error()).name, QMessageBox.Ok)
            else:
                dlpath, _ = QFileDialog.getSaveFileName(self, 'Save File', link.split('/')[-1])
                if dlpath != '':
                    self.directdl_win = DirectDownload(parent=self)
                    self.directdl = DownloadThread(link_url=link, dl_path=dlpath)
                    self.directdl.dlComplete.connect(self.directdl_win.download_complete)
                    if sys.platform.startswith('linux'):
                        self.directdl.dlComplete.connect(lambda: self.notify(qApp.applicationName(),
                                                                             'Download complete',
                                                                             self.NotifyIcon.SUCCESS))
                    else:
                        self.directdl.dlComplete.connect(lambda: QMessageBox.information(self, qApp.applicationName(),
                                                                                         'Download complete',
                                                                                         QMessageBox.Ok))
                    self.directdl.dlProgressTxt.connect(self.directdl_win.update_progress_label)
                    self.directdl.dlProgress.connect(self.directdl_win.update_progress)
                    self.directdl_win.cancelDownload.connect(self.cancel_download)
                    self.directdl.start()
                    self.hosters_win.close()

    def _init_notification_icons(self):
        for icon in self.NotifyIcon:
            icon_file = QPixmap(icon.value, 'PNG')
            icon_file.save(os.path.join(FixedSettings.config_path, os.path.basename(icon.value)), 'PNG', 100)

    def notify(self, title: str, msg: str = '', icon: Enum = None, urgency: int = 1) -> bool:
        icon_path = icon.value if icon is not None else self.NotifyIcon.DEFAULT.value
        icon_path = os.path.join(FixedSettings.config_path, os.path.basename(icon_path))
        if not os.path.exists(icon_path):
            self._init_notification_icons()
        notification = notify.Notification(title, msg, icon_path)
        notification.set_urgency(urgency)
        return notification.show()

    def cmdexec(self, cmd: str) -> bool:
        self.proc = QProcess()
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        if hasattr(self.proc, 'errorOccurred'):
            self.proc.errorOccurred.connect(lambda error: print('Process error = %s' % self.ProcError(error).name))
        if self.proc.state() == QProcess.NotRunning:
            self.proc.start(cmd)
            self.proc.waitForFinished(-1)
            rc = self.proc.exitStatus() == QProcess.NormalExit and self.proc.exitCode() == 0
            self.proc.deleteLater()
            return rc
        return False

    @pyqtSlot()
    def cancel_download(self) -> None:
        self.directdl.cancel_download = True
        self.directdl.quit()
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
                                           link_url=link, action=RealDebridThread.RealDebridAction.UNRESTRICT_LINK)
        if download:
            self.realdebrid.unrestrictedLink.connect(self.download_link)
        else:
            self.realdebrid.unrestrictedLink.connect(self.copy_download_link)
        self.realdebrid.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        if hasattr(self, 'scrapeThread'):
            if not sip.isdeleted(self.scrapeThread) and self.scrapeThread.isRunning():
                self.scrapeThread.requestInterruption()
                self.scrapeThread.quit()
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
    organizationDomain = 'http://tvlinker.ozmartians.com'
    windowSize = QSize(1000, 785)
    linksPerPage = 20
    latest_release_url = 'https://github.com/ozmartian/tvlinker/releases/latest'
    realdebrid_api_url = 'https://api.real-debrid.com/rest/1.0'
    config_path = None

    @staticmethod
    def get_app_settings() -> QSettings:
        FixedSettings.config_path = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        settings_ini = os.path.join(FixedSettings.config_path, '%s.ini' % FixedSettings.applicationName.lower())
        if not os.path.exists(settings_ini):
            os.makedirs(FixedSettings.config_path, exist_ok=True)
            QFile.copy(':%s.ini' % FixedSettings.applicationName.lower(), settings_ini)
            QFile.setPermissions(settings_ini, QFile.ReadOwner | QFile.WriteOwner)
        return QSettings(settings_ini, QSettings.IniFormat)


def main():
    app = QApplication(sys.argv)
    app.setStyle(OverrideStyle())
    app.setApplicationName(FixedSettings.applicationName)
    app.setOrganizationDomain(FixedSettings.organizationDomain)
    app.setApplicationVersion(FixedSettings.applicationVersion)
    app.setQuitOnLastWindowClosed(True)
    app.setAttribute(Qt.AA_NativeWindows, True)
    tvlinker = TVLinker(FixedSettings.get_app_settings())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
