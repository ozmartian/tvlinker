#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from urllib.request import Request, urlopen

from PyQt5.QtCore import QFile, QModelIndex, QSettings, QSize, QTextStream, QUrl, Qt, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QColor, QDesktopServices, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QDialog, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, qApp)
from bs4 import BeautifulSoup
from waitingspinnerwidget import QtWaitingSpinner

import assets


class TVLinker(QDialog):
    def __init__(self, parent=None):
        super(TVLinker, self).__init__(parent)
        self.init_settings()
        self.init_stylesheet()
        layout = QVBoxLayout()
        layout.addLayout(self.init_form())
        layout.addWidget(self.init_table())
        self.init_spinner()
        self.setLayout(layout)
        self.setWindowTitle(qApp.applicationName())
        self.setWindowIcon(QIcon(self.get_path('%s.png' % qApp.applicationName().lower())))
        self.resize(1000, 800)
        self.show()
        self.scrape_links()

    def init_settings(self) -> None:
        self.settings = QSettings(self.get_path('%s.ini' % qApp.applicationName().lower()), QSettings.IniFormat)
        self.source_url = self.settings.value('source_url')
        self.user_agent = self.settings.value('user_agent')
        self.dl_pagecount = int(self.settings.value('dl_pagecount'))

    def init_stylesheet(self) -> None:
        qApp.setStyle('Fusion')
        QFontDatabase.addApplicationFont(self.get_path('OpenSans.ttf'))
        qss = QFile(self.get_path('%s.qss' % qApp.applicationName().lower()))
        qss.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(qss)
        qApp.setStyleSheet(stream.readAll())

    def init_form(self) -> QHBoxLayout:
        self.search_field = QLineEdit(self, clearButtonEnabled=True,
                                      placeholderText='Enter search criteria')
        self.search_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.search_field.textChanged.connect(self.filter_table)
        self.refresh_button = QPushButton(QIcon.fromTheme('view-refresh'), ' Refresh', cursor=Qt.PointingHandCursor,
                                          iconSize=QSize(12, 12), clicked=self.scrape_links)
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Search:'))
        layout.addWidget(self.search_field)
        layout.addWidget(self.refresh_button)
        return layout

    def init_table(self) -> QTableWidget:
        self.table = QTableWidget(0, 4, self)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.hideColumn(1)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.viewport().setAttribute(Qt.WA_Hover)
        self.table.setHorizontalHeaderLabels(('Date', 'URL', 'Description', 'Media'))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.sortByColumn(0, Qt.DescendingOrder)
        self.table.doubleClicked.connect(self.open_link)
        return self.table

    def init_spinner(self) -> None:
        self.spinner = QtWaitingSpinner(self.table, centerOnParent=True, disableParentWhenSpinning=True,
                                        modality=Qt.ApplicationModal)
        self.spinner.setRoundness(40.0)
        self.spinner.setMinimumTrailOpacity(5.0)
        self.spinner.setTrailFadePercentage(55.0)
        self.spinner.setNumberOfLines(50)
        self.spinner.setLineLength(120)
        self.spinner.setLineWidth(5)
        self.spinner.setInnerRadius(20)
        self.spinner.setRevolutionsPerSecond(1)
        self.spinner.setColor(QColor(106, 69, 114))

    def scrape_links(self) -> str:
        self.spinner.start()
        self.setCursor(Qt.BusyCursor)
        if self.table.rowCount() > 0:
            self.table.clearContents()
            self.table.setRowCount(0)
        qApp.processEvents()
        self.table.setSortingEnabled(False)
        row = 0
        for page in range(1, self.dl_pagecount):
            url = self.source_url % page
            req = Request(url, headers={'User-agent': self.user_agent})
            res = urlopen(req)
            bs = BeautifulSoup(res.read(), 'lxml')
            links = bs.find_all('table', class_='posts_table')
            self.table.setRowCount(self.table.rowCount() + len(links))
            for link_table in links:
                cols = link_table.tr.find_all('td')
                table_row = [
                    cols[2].get_text(),
                    cols[1].find('a').get('href'),
                    cols[1].find('a').get_text(),
                    cols[0].find('a').get_text().replace('TV-', '')
                ]
                col = 0
                qApp.processEvents()
                for item in table_row:
                    table_item = QTableWidgetItem(item)
                    table_item.setToolTip(table_row[1])
                    table_item.setFont(QFont('Open Sans', weight=QFont.Normal))
                    if col == 2:
                        table_item.setFont(QFont('Open Sans', pointSize=11, weight=QFont.DemiBold))
                        table_item.setText('    ' + table_item.text())
                    elif col == 3:
                        table_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, table_item)
                    qApp.processEvents()
                    col += 1
                row += 1
            qApp.processEvents()
        self.table.setSortingEnabled(True)
        self.spinner.stop()
        self.setCursor(Qt.PointingHandCursor)

    @pyqtSlot(QModelIndex)
    def open_link(self, index: QModelIndex) -> bool:
        return QDesktopServices.openUrl(QUrl(self.table.item(self.table.currentRow(), 1).text()))

    @pyqtSlot(str)
    def filter_table(self, text: str) -> None:
        valid_rows = []
        for item in self.table.findItems(text, Qt.MatchContains):
            valid_rows.append(item.row())
        for row in range(0, self.table.rowCount()):
            if row not in valid_rows:
                self.table.hideRow(row)
            else:
                self.table.showRow(row)

    def get_path(self, path: str = None) -> str:
        return ':assets/%s' % path
        # if getattr(sys, 'frozen', False):
        #     return os.path.join(sys._MEIPASS, path)
        # return os.path.join(QFileInfo(__file__).absolutePath(), path)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.table.deleteLater()
        self.deleteLater()
        qApp.quit()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('ozmartians.com')
    app.setApplicationName('TVLinker')
    tv = TVLinker()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
