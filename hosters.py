#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSize, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QDesktopServices, QHideEvent, QIcon, QPixmap, QShowEvent
from PyQt5.QtWidgets import (QBoxLayout, QButtonGroup, QDialog, QFrame, QHBoxLayout, QLabel, QProgressBar,
                             QPushButton, QSizePolicy, QVBoxLayout, qApp)


class HosterLinks(QDialog):

    downloadLink = pyqtSignal(str)
    copyLink = pyqtSignal(str)

    def __init__(self, parent, f=Qt.Tool):
        super(QDialog, self).__init__(parent, f)
        self.parent = parent
        self.setWindowModality(Qt.ApplicationModal)
        self.hosters = []
        self.setContentsMargins(20, 20, 20, 20)
        self.layout = QVBoxLayout(spacing=25)
        self.setLayout(self.layout)
        self.copy_icon = QIcon(self.parent.get_path('images/copy_icon.png'))
        self.open_icon = QIcon(self.parent.get_path('images/open_icon.png'))
        self.download_icon = QIcon(self.parent.get_path('images/download_icon.png'))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.copy_group = QButtonGroup(exclusive=False)
        self.copy_group.buttonClicked[int].connect(self.copy_link)
        self.open_group = QButtonGroup(exclusive=False)
        self.open_group.buttonClicked[int].connect(self.open_link)
        self.download_group = QButtonGroup(exclusive=False)
        self.download_group.buttonClicked[int].connect(self.download_link)
        self.setWindowTitle('Hoster Links')

    def clear_layout(self, layout: QBoxLayout = None) -> None:
        if layout is None:
            layout = self.layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())
        self.layout.setSpacing(25)

    @staticmethod
    def get_separator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def show_hosters(self, hosters: list) -> None:
        self.hosters = hosters
        self.clear_layout()
        index = 0
        for hoster in hosters:
            hoster_logo = QLabel(pixmap=QPixmap(self.parent.get_path('images/hoster_%s' % QUrl(hoster[0]).fileName())), toolTip=hoster[1])
            hoster_logo.setMinimumWidth(160)
            hoster_logo.setAlignment(Qt.AlignCenter)
            copy_btn = QPushButton(self, icon=self.copy_icon, text=' COPY', toolTip='Copy to clipboard', flat=False,
                                   cursor=Qt.PointingHandCursor, iconSize=QSize(16, 16))
            copy_btn.setFixedSize(90, 30)
            self.copy_group.addButton(copy_btn, index)
            open_btn = QPushButton(self, icon=self.open_icon, text=' OPEN', toolTip='Open in browser', flat=False,
                                   cursor=Qt.PointingHandCursor, iconSize=QSize(16, 16))
            open_btn.setFixedSize(90, 30)
            self.open_group.addButton(open_btn, index)
            download_btn = QPushButton(self, icon=self.download_icon, text=' DOWNLOAD', toolTip='Download link',
                                            flat=False, cursor=Qt.PointingHandCursor, iconSize=QSize(16, 16))
            download_btn.setFixedSize(110, 30)
            self.download_group.addButton(download_btn, index)
            layout = QHBoxLayout(spacing=10)
            layout.addWidget(hoster_logo)
            layout.addWidget(copy_btn, Qt.AlignRight)
            layout.addWidget(open_btn, Qt.AlignRight)
            layout.addWidget(download_btn, Qt.AlignRight)
            self.layout.addLayout(layout)
            if self.layout.count() <= len(hosters):
                self.layout.addWidget(self.get_separator())
            index += 1
        qApp.restoreOverrideCursor()
        qApp.processEvents()
        self.adjustSize()

    @pyqtSlot(int)
    def copy_link(self, button_id: int) -> None:
        self.copyLink.emit(self.hosters[button_id][1])

    @pyqtSlot(int)
    def open_link(self, button_id: int) -> None:
        QDesktopServices.openUrl(QUrl(self.hosters[button_id][1]))
        self.hide()

    @pyqtSlot(int)
    def download_link(self, button_id: int) -> None:
        self.downloadLink.emit(self.hosters[button_id][1])

    def hideEvent(self, event: QHideEvent) -> None:
        self.clear_layout()
        super(QDialog, self).hideEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        busy_label = QLabel('Retrieving hoster links...', alignment=Qt.AlignCenter)
        busy_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        busy_indicator = QProgressBar(parent=self, minimum=0, maximum=0)
        self.layout.setSpacing(10)
        self.layout.addWidget(busy_label)
        self.layout.addWidget(busy_indicator)
        self.adjustSize()
        self.setMinimumWidth(485)
        super(HosterLinks, self).showEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide()
        event.accept()
