#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, qApp, QMessageBox


class DirectDownload(QDialog):
    cancelDownload = pyqtSignal()

    def __init__(self, parent, f=Qt.WindowCloseButtonHint):
        super(DirectDownload, self).__init__(parent, f)
        self.parent = parent
        self.setWindowTitle('Download Progress')
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(485)
        self.setContentsMargins(20, 20, 20, 20)
        layout = QVBoxLayout()
        self.progress_label = QLabel(alignment=Qt.AlignCenter)
        self.progress = QProgressBar(self.parent)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

    @pyqtSlot(int)
    def update_progress(self, progress: int) -> None:
        self.progress.setValue(progress)

    @pyqtSlot(str)
    def update_progress_label(self, progress_txt: str) -> None:
        if not self.isVisible():
            self.show()
        self.progress_label.setText(progress_txt)

    @pyqtSlot()
    def download_complete(self) -> None:
        qApp.restoreOverrideCursor()
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        qApp.restoreOverrideCursor()
        self.cancelDownload.emit()
        super(DirectDownload, self).closeEvent(event)
