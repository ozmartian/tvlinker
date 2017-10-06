#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtDBus import QDBusConnection, QDBusMessage
from PyQt5.QtWidgets import qApp, QWidget


class TaskbarProgress(QWidget):
    def __init__(self, parent=None):
        super(TaskbarProgress, self).__init__(parent)
        self._desktopfile = 'application://{}.desktop'.format(qApp.applicationName().lower())
        self.clear()

    @pyqtSlot()
    def clear(self):
        self.setProgress(0.0, False)

    @pyqtSlot(float, bool)
    def setProgress(self, value: float, visible: bool=True):
        sessionbus = QDBusConnection.sessionBus()
        signal = QDBusMessage.createSignal('/com/canonical/unity/launcherentry/337963624',
                                           'com.canonical.Unity.LauncherEntry', 'Update')
        message = signal << self._desktopfile << {'progress-visible': visible, 'progress': value}
        sessionbus.send(message)
