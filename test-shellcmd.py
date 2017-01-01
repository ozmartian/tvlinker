#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, QProcess
from PyQt5.QtWidgets import QTextEdit, QApplication
import sys


class MyQProcess(QProcess):
    def __init__(self):
        # Call base class method
        QProcess.__init__(self)
        # Create an instance variable here (of type QTextEdit)
        self.edit = QTextEdit()
        self.edit.setWindowTitle("QTextEdit Standard Output Redirection")
        self.edit.show()

        # Define Slot Here

    @pyqtSlot()
    def readStdOutput(self):
        self.edit.append(str(self.readAllStandardOutput(), 'utf-8'))


def main():
    app = QApplication(sys.argv)
    qProcess = MyQProcess()
    qProcess.setProcessChannelMode(QProcess.MergedChannels)
    qProcess.start("sudo fsck -fy /dev/sda6")
    qProcess.readyReadStandardOutput.connect(qProcess.readStdOutput)
    return app.exec_()


if __name__ == '__main__':
    main()
