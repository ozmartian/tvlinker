#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtDBus import QDBusConnection, QDBusMessage
from PyQt5.QtWidgets import qApp, QWidget


class TaskbarProgress(QWidget):
    def __init__(self, parent=None):
        super(TaskbarProgress, self).__init__(parent)
        self.parent = parent
        self._desktopFileName = '%s.desktop' % qApp.applicationName().lower()
        self._sessionbus = QDBusConnection.sessionBus()
        self.clear()

    @pyqtSlot()
    def clear(self):
        self.setProgress(False, 0.0)

    @pyqtSlot(float, bool)
    def setProgress(self, showprogress: bool, progressvalue: float):
        signal = QDBusMessage.createSignal('/com/canonical/unity/launcherentry/337963624',
                                           'com.canonical.Unity.LauncherEntry', 'Update')
        message = signal << 'application://{0}'.format(self._desktopFileName) << {
            'progress-showprogress': showprogress,
            'progress': progressvalue
        }
        self._sessionbus.send(message)
