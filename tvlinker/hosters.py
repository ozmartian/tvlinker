#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup, SoupStrainer, Tag

from PyQt5.QtCore import QSize, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QDesktopServices, QIcon
from PyQt5.QtWidgets import (QButtonGroup, QDialog, QGroupBox, QHBoxLayout, QLabel, QProgressDialog,
                             QProxyStyle, QPushButton, QScrollArea, QSizePolicy, QStyle, QStyleFactory, QVBoxLayout,
                             QWidget, qApp)


# noinspection PyMethodOverriding
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

    def __init__(self, parent, f=Qt.WindowCloseButtonHint):
        super(HosterLinks, self).__init__(parent, f)
        self.parent = parent
        self.loading_progress = QProgressDialog('Retrieving hoster links...', None, 0, 0, self.parent,
                                                Qt.WindowCloseButtonHint)
        self.loading_progress.setStyle(QStyleFactory.create('Fusion'))
        self.loading_progress.setWindowTitle('Hoster Links')
        self.loading_progress.setMinimumWidth(485)
        self.loading_progress.setWindowModality(Qt.ApplicationModal)
        self.loading_progress.show()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.setMaximumHeight(700)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
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

    def show_hosters(self, titles: list, links: list) -> None:
        self.titles = titles
        self.links = links
        self.loading_progress.cancel()
        self.setMinimumWidth(850)
        hosterswidget_layout = QVBoxLayout()
        for title in titles:
            title_label = QLabel(HosterLinks.bs_tag_to_string(title), self)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet('QLabel { font-size:13px; }')
            title_layout = QHBoxLayout()
            title_layout.setSpacing(10)
            title_layout.addStretch(1)
            link_bs = self.links[titles.index(title)]
            bs = BeautifulSoup(HosterLinks.bs_tag_to_string(link_bs), 'lxml', parse_only=SoupStrainer('a'))
            for anchor in bs:
                link = anchor['href']
                hoster_name = HosterLinks.get_hoster_name(link)
                hoster_btn = QPushButton(self)
                hoster_btn.setFlat(True)
                hoster_btn.setToolTip(hoster_name)
                hoster_btn.setCursor(Qt.PointingHandCursor)
                hoster_btn.setIcon(QIcon(self.parent.get_path('images/hosters/%s.png' % hoster_name)))
                hoster_btn.setIconSize(QSize(120, 26))
                title_layout.addWidget(hoster_btn)
            title_layout.addStretch(1)
            hoster_layout = QVBoxLayout()
            hoster_layout.addWidget(title_label)
            hoster_layout.addSpacing(15)
            hoster_layout.addLayout(title_layout)
            groupbox = QGroupBox(self)
            groupbox.setObjectName('hosters')
            groupbox.setContentsMargins(0, 0, 0, 0)
            groupbox.setLayout(hoster_layout)
            hosterswidget_layout.addWidget(groupbox)
        hosters_widget = QWidget(self)
        hosters_widget.setLayout(hosterswidget_layout)
        scrollarea = QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollarea.setWidget(hosters_widget)
        self.layout.addWidget(scrollarea)

        # if self.title is not None:
        #     title_label = QLabel(self.title, self)
        #     title_label.setObjectName('heading')
        #     title_label.setAlignment(Qt.AlignCenter)
        #     title_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        #     self.layout.addWidget(title_label)
        #
        # for hoster in hosters:
        #     index = hosters.index(hoster)
        #     hoster_name = HosterLinks.get_hoster_name(self.hosters[index])
        #     hoster_logo = QLabel(self)
        #     hoster_logo.setPixmap(QPixmap(self.parent.get_path('images/hosters/%s.png' % hoster_name)))
        #     hoster_logo.setToolTip(hoster_name)
        #     hoster_logo.setMinimumWidth(285)
        #     hoster_logo.setAlignment(Qt.AlignCenter)
        #
        #     copy_btn = QPushButton(self.copy_icon, ' COPY', self)
        #     copy_btn.setToolTip('Copy to clipboard')
        #     copy_btn.setCursor(Qt.PointingHandCursor)
        #     copy_btn.setDefault(False)
        #     copy_btn.setAutoDefault(False)
        #     copy_btn.setStyle(OverrideStyle())
        #     copy_btn.setStyleSheet('padding:2px 10px;')
        #     copy_btn.setMinimumHeight(35)
        #     self.copy_group.addButton(copy_btn, index)
        #
        #     open_btn = QPushButton(self.open_icon, ' OPEN', self)
        #     open_btn.setToolTip('Open in browser')
        #     open_btn.setCursor(Qt.PointingHandCursor)
        #     open_btn.setDefault(False)
        #     open_btn.setAutoDefault(False)
        #     open_btn.setStyle(OverrideStyle())
        #     open_btn.setStyleSheet('padding:2px 10px;')
        #     open_btn.setMinimumHeight(35)
        #     self.open_group.addButton(open_btn, index)
        #
        #     download_btn = QPushButton(self.download_icon, ' DOWNLOAD', self)
        #     download_btn.setToolTip('Download link')
        #     download_btn.setCursor(Qt.PointingHandCursor)
        #     download_btn.setDefault(False)
        #     download_btn.setAutoDefault(False)
        #     download_btn.setStyle(OverrideStyle())
        #     download_btn.setStyleSheet('padding:2px 10px;')
        #     download_btn.setMinimumHeight(35)
        #     self.download_group.addButton(download_btn, index)
        #
        #     actions_layout = QHBoxLayout()
        #     actions_layout.setSpacing(10)
        #     actions_layout.addStretch(1)
        #     actions_layout.addWidget(hoster_logo)
        #     actions_layout.addStretch(1)
        #     actions_layout.addWidget(copy_btn)
        #     actions_layout.addWidget(open_btn)
        #     actions_layout.addWidget(download_btn)
        #     actions_layout.addStretch(1)
        #
        #     groupbox = QGroupBox(self)
        #     groupbox.setObjectName('hosters')
        #     groupbox.setContentsMargins(6, 6, 6, 6)
        #     groupbox.setLayout(actions_layout)
        #     self.layout.addWidget(groupbox)

        self.show()
        qApp.restoreOverrideCursor()

    @staticmethod
    def bs_tag_to_string(bstag: Tag) -> str:
        return ''.join(str(item) for item in bstag.contents)

    @staticmethod
    def get_hoster_name(link: str) -> str:
        name = QUrl(link).host().replace('www.', '').replace('.com', '').replace('.net', '') \
            .replace('.org', '').replace('.co', '')
        return 'uploaded' if name == 'ul.to' else name

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
