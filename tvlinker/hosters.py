#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QDesktopServices, QIcon, QPixmap
from PyQt5.QtWidgets import (QButtonGroup, QDialog, QGroupBox, QHBoxLayout, QLabel, QProgressDialog,
                             QProxyStyle, QPushButton, QSizePolicy, QStyle, QStyleFactory, QVBoxLayout,
                             qApp)


class OverrideStyle(QProxyStyle):
    def __init__(self, key: str = 'Fusion'):
        super(OverrideStyle, self).__init__(key)
        self.setBaseStyle(QStyleFactory.create(key))

    def styleHint(self, hint, option, widget, returnData) -> int:
        if hint in (QStyle.SH_UnderlineShortcut, QStyle.SH_DialogButtons_DefaultButton):
            return 0
        return super(OverrideStyle, self).styleHint(hint, option, widget, returnData)


class HosterLinks(QDialog):
    downloadLink = pyqtSignal(str)
    copyLink = pyqtSignal(str)

    def __init__(self, parent, title=None, f=Qt.WindowCloseButtonHint):
        super(HosterLinks, self).__init__(parent, f)
        self.parent = parent
        self.loading_progress = QProgressDialog('Retrieving hoster links...', None, 0, 0,
                                                self.parent, Qt.WindowCloseButtonHint)
        self.loading_progress.setStyle(QStyleFactory.create('Fusion'))
        self.loading_progress.setWindowTitle('Hoster Links')
        self.loading_progress.setMinimumWidth(485)
        self.loading_progress.setWindowModality(Qt.ApplicationModal)
        self.loading_progress.show()
        self.title = title
        self.hosters = []
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setWindowTitle('Hoster Links')
        self.setWindowModality(Qt.ApplicationModal)
        self.copy_icon = QIcon(self.parent.get_path('images/copy_icon.png'))
        self.open_icon = QIcon(self.parent.get_path('images/open_icon.png'))
        self.download_icon = QIcon(self.parent.get_path('images/download_icon.png'))
        self.copy_group = QButtonGroup(exclusive=False)
        self.copy_group.buttonClicked[int].connect(self.copy_link)
        self.open_group = QButtonGroup(exclusive=False)
        self.open_group.buttonClicked[int].connect(self.open_link)
        self.download_group = QButtonGroup(exclusive=False)
        self.download_group.buttonClicked[int].connect(self.download_link)

    def show_hosters(self, hosters: list) -> None:
        self.hosters = hosters
        self.loading_progress.cancel()
        self.setMinimumWidth(650)
        if self.title is not None:
            title_label = QLabel(self.title, alignment=Qt.AlignCenter, objectName='heading')
            title_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
            self.layout.addWidget(title_label)
        for hoster in hosters:
            index = hosters.index(hoster)
            hoster_name = self.get_hoster_name(self.hosters[index])
            hoster_logo = QLabel(pixmap=QPixmap(self.parent.get_path('images/hoster_%s.png' % hoster_name)),
                                 toolTip=hoster_name)
            hoster_logo.setMinimumWidth(285)
            hoster_logo.setAlignment(Qt.AlignCenter)
            copy_btn = QPushButton(self, icon=self.copy_icon, text=' COPY', toolTip='Copy to clipboard',
                                   autoDefault=False, default=False, cursor=Qt.PointingHandCursor)
            copy_btn.setStyle(OverrideStyle())
            copy_btn.setStyleSheet('padding:2px 10px;')
            copy_btn.setMinimumHeight(35)
            self.copy_group.addButton(copy_btn, index)
            open_btn = QPushButton(self, icon=self.open_icon, text=' OPEN', toolTip='Open in browser',
                                   autoDefault=False, default=False, cursor=Qt.PointingHandCursor)
            open_btn.setStyle(OverrideStyle())
            open_btn.setStyleSheet('padding:2px 10px;')
            open_btn.setMinimumHeight(35)
            self.open_group.addButton(open_btn, index)
            download_btn = QPushButton(self, icon=self.download_icon, text=' DOWNLOAD', toolTip='Download link',
                                       autoDefault=False, default=False, cursor=Qt.PointingHandCursor)
            download_btn.setStyle(OverrideStyle())
            download_btn.setStyleSheet('padding:2px 10px;')
            download_btn.setMinimumHeight(35)
            self.download_group.addButton(download_btn, index)

            actions_layout = QHBoxLayout(spacing=10)
            actions_layout.addStretch(1)
            actions_layout.addWidget(hoster_logo)
            actions_layout.addStretch(1)
            actions_layout.addWidget(copy_btn)
            actions_layout.addWidget(open_btn)
            actions_layout.addWidget(download_btn)
            actions_layout.addStretch(1)

            groupbox = QGroupBox(self, objectName='hosters')
            groupbox.setContentsMargins(6, 6, 6, 6)
            groupbox.setLayout(actions_layout)
            self.layout.addWidget(groupbox)
        self.show()
        qApp.restoreOverrideCursor()

    def get_hoster_name(self, link: str) -> str:
        return QUrl(link).host().replace('www.', '').replace('.com', '').replace('.net', '')

    @pyqtSlot(int)
    def copy_link(self, button_id: int) -> None:
        self.copyLink.emit(self.hosters[button_id])

    @pyqtSlot(int)
    def open_link(self, button_id: int) -> None:
        QDesktopServices.openUrl(QUrl(self.hosters[button_id]))
        self.close()

    @pyqtSlot(int)
    def download_link(self, button_id: int) -> None:
        self.downloadLink.emit(self.hosters[button_id])

    def closeEvent(self, event: QCloseEvent) -> None:
        self.deleteLater()
        qApp.restoreOverrideCursor()
        super(QDialog, self).closeEvent(event)
