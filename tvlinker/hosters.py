#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from bs4 import BeautifulSoup, SoupStrainer, Tag

from PyQt5.QtCore import QSize, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QColor, QDesktopServices, QIcon, QPalette
from PyQt5.QtWidgets import (QDialog, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QMenu, QProgressBar,
                             QProgressDialog, QPushButton, QScrollArea, QSizePolicy, QStyleFactory,
                             QVBoxLayout, QWidget, qApp)


class HosterLinks(QDialog):
    downloadLink = pyqtSignal(str)
    copyLink = pyqtSignal(str)

    def __init__(self, parent, f=Qt.WindowCloseButtonHint):
        super(HosterLinks, self).__init__(parent, f)
        self.parent = parent
        self.setObjectName('hosters')
        self.loading_progress = HosterProgress('Retrieving hoster links...', 0, 0, self.parent,
                                               Qt.WindowCloseButtonHint)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.setLayout(self.layout)
        self.setWindowTitle('Hoster Links')
        self.setWindowModality(Qt.ApplicationModal)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def show_hosters(self, links: list) -> None:
        self.links = links
        self.loading_progress.cancel()
        hosterswidget_layout = QVBoxLayout()
        for tag in self.links:
            title_label = QLabel(HosterLinks.bs_tag_to_string(tag.find_previous('p')), self)
            title_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            title_label.setCursor(Qt.IBeamCursor)
            title_label.setOpenExternalLinks(True)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet('QLabel { margin: 0; color: #444; font-size: 14px; padding: 8px; ' +
                                      'border: 1px solid #C0C0C0; background-color: #FEFEFE; }')
            title_layout = QHBoxLayout()
            title_layout.setContentsMargins(0, 0, 0, 0)
            title_layout.setSpacing(6)
            title_layout.addStretch(1)
            bs = BeautifulSoup(HosterLinks.bs_tag_to_string(tag), 'lxml', parse_only=SoupStrainer('a'))
            for anchor in bs:
                link = anchor['href']
                hoster_name = HosterLinks.get_hoster_name(link)
                menu = QMenu(self)
                menu.setCursor(Qt.PointingHandCursor)
                menu.addAction('  COPY LINK', lambda dl=link: self.copy_link(dl), 0)
                menu.addAction('  OPEN LINK', lambda dl=link: self.open_link(dl), 0)
                menu.addAction(' DOWNLOAD', lambda dl=link: self.download_link(dl), 0)
                shadow = QGraphicsDropShadowEffect()
                shadow.setColor(Qt.gray)
                shadow.setBlurRadius(10)
                shadow.setOffset(2, 2)
                hoster_btn = QPushButton(self)
                hoster_btn.setStyle(QStyleFactory.create('Fusion'))
                hoster_btn.setGraphicsEffect(shadow)
                hoster_btn.setDefault(False)
                hoster_btn.setAutoDefault(False)
                hoster_btn.setToolTip(hoster_name)
                hoster_btn.setCursor(Qt.PointingHandCursor)
                hoster_btn.setIcon(QIcon(self.parent.get_path('images/hosters/%s.png' % hoster_name)))
                hoster_btn.setIconSize(QSize(100, 21))
                hoster_btn.setStyleSheet('''
                    QPushButton {
                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                          stop: 0 #FEFEFE, stop: 1 #FAFAFA);
                        padding: 6px 0;
                        border-radius: 0;
                        border: 1px solid #B9B9B9;
                    }
                    QPushButton:hover {
                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                          stop: 0 #B9B9B9, stop: 1 #DADBDE);
                    }
                    QPushButton:pressed {
                        border: 1px inset #B9B9B9;
                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                          stop: 0 #DADBDE, stop: 1 #B9B9B9);
                    }
                    QPushButton::menu-indicator { left: -2000px; }
                ''')
                menu.setFixedWidth(118)
                menu.setStyleSheet('''
                    QMenu {
                        border-radius: 0;
                        border: 1px solid #C0C2C3;
                        background-color: #FAFAFA;
                        color: #4C4C4C;
                    }
                    QMenu::item { text-align: center; }
                    QMenu::item:selected, QMenu::item:hover { background-color: #6A687D; color: #FFF; }''')
                hoster_btn.setMenu(menu)
                title_layout.addWidget(hoster_btn)
            title_layout.addStretch(1)
            hoster_layout = QVBoxLayout()
            hoster_layout.addWidget(title_label)
            hoster_layout.addLayout(title_layout)
            hosterswidget_layout.addLayout(hoster_layout)
            hosterswidget_layout.addSpacing(15)

        stretch_layout = QHBoxLayout()
        stretch_layout.addStretch(1)
        stretch_layout.addLayout(hosterswidget_layout)
        stretch_layout.addStretch(1)
        hosters_widget = QWidget(self)
        hosters_widget.setLayout(stretch_layout)
        scrollarea = QScrollArea(self)
        scrollarea.setFrameShape(QScrollArea.NoFrame)
        scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollarea.setWidget(hosters_widget)
        scrollarea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scrollarea.setMinimumWidth(hosters_widget.geometry().width() + 20)
        self.layout.addWidget(scrollarea)
        w = scrollarea.width() + 15
        h = hosters_widget.geometry().height() + 10
        self.setFixedSize(w if w <= 810 else 810, h if h <= 750 else 750)
        self.show()
        qApp.restoreOverrideCursor()

    @staticmethod
    def bs_tag_to_string(bstag: Tag) -> str:
        return ''.join(str(item) for item in bstag.contents)

    @staticmethod
    def get_hoster_name(link: str) -> str:
        name = QUrl(link).host().replace('www.', '').replace('.com', '').replace('.net', '') \
            .replace('.org', '').replace('.co', '')
        if name == 'businessnewscurrent.online':
            name = 'cloudyfiles'
        return 'uploaded' if name == 'ul.to' else name

    @pyqtSlot(str)
    def copy_link(self, link: str) -> None:
        self.copyLink.emit(link)

    @pyqtSlot(str)
    def open_link(self, link: str) -> None:
        QDesktopServices.openUrl(QUrl(link))
        self.close()

    @pyqtSlot(str)
    def download_link(self, link: str) -> None:
        self.downloadLink.emit(link)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.loading_progress.cancel()
        self.deleteLater()
        qApp.restoreOverrideCursor()
        super(QDialog, self).closeEvent(event)


class HosterProgress(QProgressDialog):
    def __init__(self, label: str, minval: int, maxval: int, parent: QWidget, flags: Qt.WindowFlags):
        super(HosterProgress, self).__init__(label, None, minval, maxval, parent, flags)
        self.setWindowTitle('Hoster Links')
        self.setMinimumWidth(485)
        self.setWindowModality(Qt.ApplicationModal)
        self.setLabelText(label)
        bar = QProgressBar(self)
        bar.setRange(minval, maxval)
        bar.setValue(minval)
        bar.setStyle(QStyleFactory.create('Fusion'))
        p = bar.palette()
        p.setColor(QPalette.Highlight, QColor(100, 44, 104, 185))
        bar.setPalette(p)
        self.setBar(bar)
        self.show()
