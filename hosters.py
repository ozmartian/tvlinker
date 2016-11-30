#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtCore import QTimer, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QDesktopServices, QIcon, QPixmap
from PyQt5.QtWidgets import (QBoxLayout, QButtonGroup, QDialog, QFrame, QGroupBox, QHBoxLayout, QLabel, QLayout,
                             QProgressBar, QPushButton, QSizePolicy, QSpacerItem, QStyleFactory, QVBoxLayout, qApp)


class HosterLinks(QDialog):
    downloadLink = pyqtSignal(str)
    copyLink = pyqtSignal(str)

    def __init__(self, parent, title=None, f=Qt.WindowCloseButtonHint):
        super(HosterLinks, self).__init__(parent, f)
        self.parent = parent
        self.title = title
        self.setWindowModality(Qt.ApplicationModal)
        self.hosters = []
        self.layout = QVBoxLayout(spacing=15)
        self.layout.setContentsMargins(20, 10, 20, 20)
        self.setLayout(self.layout)
        self.copy_icon = QIcon(self.parent.get_path('images/copy_icon.png'))
        self.open_icon = QIcon(self.parent.get_path('images/open_icon.png'))
        self.download_icon = QIcon(self.parent.get_path('images/download_icon.png'))
        # self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.copy_group = QButtonGroup(exclusive=False)
        self.copy_group.buttonClicked[int].connect(self.copy_link)
        self.open_group = QButtonGroup(exclusive=False)
        self.open_group.buttonClicked[int].connect(self.open_link)
        self.download_group = QButtonGroup(exclusive=False)
        self.download_group.buttonClicked[int].connect(self.download_link)
        self.setWindowTitle('Hoster Links')
        busy_label = QLabel('Retrieving hoster links...', alignment=Qt.AlignCenter)
        busy_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        busy_indicator = QProgressBar(None, minimum=0, maximum=0)
        busy_indicator.setStyle(QStyleFactory.create('Fusion'))
        self.layout.addWidget(busy_label)
        self.layout.addSpacerItem(QSpacerItem(1, 10))
        self.layout.addWidget(busy_indicator)
        self.setMinimumWidth(485)

    def clear_layout(self, layout: QBoxLayout = None) -> None:
        if layout is None:
            layout = self.layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    def show_hosters(self, hosters: list) -> None:
        self.hosters = hosters
        self.hide()
        self.clear_layout()
        self.setMinimumWidth(650)
        if self.title is not None:
            title_label = QLabel(self.title, alignment=Qt.AlignCenter, objectName='heading')
            title_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
            self.layout.addWidget(title_label)
        index = 0
        for hoster in hosters:
            hoster_logo = QLabel(pixmap=QPixmap(self.parent.get_path('images/hoster_%s' % QUrl(hoster[0]).fileName())),
                                 toolTip=hoster[1])
            hoster_logo.setMinimumWidth(200)
            hoster_logo.setAlignment(Qt.AlignCenter)
            copy_btn = QPushButton(self, icon=self.copy_icon, text=' COPY', toolTip='Copy to clipboard',
                                   autoDefault=False, default=False, cursor=Qt.PointingHandCursor)
            copy_btn.setMinimumHeight(35)
            copy_btn.setStyle(QStyleFactory.create('Fusion'))
            self.copy_group.addButton(copy_btn, index)
            open_btn = QPushButton(self, icon=self.open_icon, text=' OPEN', toolTip='Open in browser',
                                   autoDefault=False, default=False, cursor=Qt.PointingHandCursor)
            open_btn.setMinimumHeight(35)
            open_btn.setStyle(QStyleFactory.create('Fusion'))
            self.open_group.addButton(open_btn, index)
            download_btn = QPushButton(self, icon=self.download_icon, text=' DOWNLOAD', toolTip='Download link',
                                       autoDefault=False, default=False, cursor=Qt.PointingHandCursor)
            download_btn.setMinimumHeight(35)
            download_btn.setStyle(QStyleFactory.create('Fusion'))
            self.download_group.addButton(download_btn, index)

            actions_layout = QHBoxLayout(spacing=10)
            actions_layout.addWidget(hoster_logo)
            actions_layout.addWidget(copy_btn, Qt.AlignRight)
            actions_layout.addWidget(open_btn, Qt.AlignRight)
            actions_layout.addWidget(download_btn, Qt.AlignRight)
            groupbox = QGroupBox(self, objectName='hosters')
            groupbox.setContentsMargins(10, 10, 10, 10)
            groupbox.setLayout(actions_layout)
            self.layout.addWidget(groupbox)
            index += 1
        QTimer.singleShot(500, self.adjustAndShow)

    def adjustAndShow(self):
        self.show()
        self.updateGeometry()
        qApp.restoreOverrideCursor()

    @pyqtSlot(int)
    def copy_link(self, button_id: int) -> None:
        self.copyLink.emit(self.hosters[button_id][1])

    @pyqtSlot(int)
    def open_link(self, button_id: int) -> None:
        QDesktopServices.openUrl(QUrl(self.hosters[button_id][1]))
        self.close()

    @pyqtSlot(int)
    def download_link(self, button_id: int) -> None:
        self.downloadLink.emit(self.hosters[button_id][1])

    def closeEvent(self, event: QCloseEvent) -> None:
        self.deleteLater()
        qApp.restoreOverrideCursor()
        super(QDialog, self).closeEvent(event)
