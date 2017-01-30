#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import shlex
import sys
from zipfile import ZipFile

from PyQt5.QtCore import QFileInfo, QProcess, QSize, pyqtSlot
from PyQt5.QtWidgets import QDialog, QMessageBox, QTextEdit, QVBoxLayout, qApp


class Downloader(QDialog):
    def __init__(self, link_url: str, dl_path: str, parent=None):
        super(Downloader, self).__init__(parent)
        self.parent = parent
        self.download_link = link_url
        self.download_path = dl_path
        if self.check_aria_install():
            self.aria2_cmd = 'aria2c'
            self.aria2_args = '-x 6 -d %s %s' % (self.download_path, self.download_link)
            self.console = QTextEdit(self.parent)
            self.console.setWindowTitle('%s Downloader' % qApp.applicationName())
            self.proc = QProcess(self.parent)
            layout = QVBoxLayout()
            layout.addWidget(self.console)
            self.setLayout(layout)
            self.setFixedSize(QSize(400, 300))
        else:
            QMessageBox.critical(self.parent, 'DOWNLOADER ERROR', '<p>The <b>aria2c</b> executable binary could not ' +
                                 'be found in your installation folders. The binary comes packaged with this ' +
                                 'application so it is likely that it was accidentally deleted via human ' +
                                 'intervntion or incorrect file permissions are preventing access to it.</p>' +
                                 '<p>You may either download and install <b>aria2</b> manually yourself, ensuring ' +
                                 'its installation location is globally accessible via PATH environmnt variables or ' +
                                 'simply reinstall this application again. If the issue is not resolved then try ' +
                                 'to download the application again incase the orignal you installed already was ' +
                                 'corrupted/broken.', buttons=QMessageBox.Close)

    def __del__(self) -> None:
        self.proc.terminate()
        if not self.proc.waitForFinished(10000):
            self.proc.kill()

    @staticmethod
    def aria_clients() -> dict:
        return {
            'darwin': {
                'target_path': Downloader.get_path('bin/aria2c'),
                'bin_archive': Downloader.get_path('bin/macOS/aria2c.zip')
            },
            'linux32': {
                'target_path': Downloader.get_path('bin/aria2c'),
                'bin_archive': Downloader.get_path('bin/linux32/aria2c.zip')
            },
            'linux64': {
                'target_path': Downloader.get_path('bin/aria2c'),
                'bin_archive': Downloader.get_path('bin/linux64/aria2c.zip')
            },
            'win32': {
                'target_path': Downloader.get_path('bin/aria2c.exe'),
                'bin_archive': Downloader.get_path('bin/win32/aria2c.zip')
            },
            'win64': {
                'target_path': Downloader.get_path('bin/aria2c.exe'),
                'bin_archive': Downloader.get_path('bin/win64/aria2c.zip')
            }
        }

    @staticmethod
    def get_machine_code() -> str:
        mcode = ''
        if sys.platform == 'darwin':
            mcode = 'macOS'
        elif sys.platform == 'win32' and platform.machine().endswith('86'):
            mcode = 'win32'
        elif sys.platform == 'win32' and platform.machine().endswith('64'):
            mcode = 'win64'
        elif sys.platform.startswith('linux') and platform.machine().endswith('86'):
            mcode = 'linux32'
        elif sys.platform.startswith('linux') and platform.machine().endswith('64'):
            mcode = 'linux64'
        return mcode

    @staticmethod
    def check_aria_install() -> bool:
        return os.path.exists(Downloader.aria_clients()[Downloader.get_machine_code()]['target_path'])

    @staticmethod
    def setup_aria() -> bool:
        aria_zip = Downloader.aria_clients()[Downloader.get_machine_code()]['bin_archive']
        aria_install = Downloader.aria_clients()[Downloader.get_machine_code()]['target_path']
        if os.path.exists(aria_zip):
            with ZipFile(aria_zip) as archive:
                target_path, target_file = os.path.split(aria_install)
                extracted_path = archive.extract(target_file, path=target_path)
                if extracted_path == aria_install and os.path.exists(extracted_path):
                    if sys.platform is not 'win32':
                        os.chmod(extracted_path, 0o755)
                    return True
        return False

    def init_proc(self) -> None:
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyRead.connect(self.console_output)
        self.proc.setProgram(self.aria2_cmd)
        self.proc.setArguments(shlex.split(self.aria2_args))

    def start(self) -> None:
        self.init_proc()
        self.show()
        self.proc.start()

    @pyqtSlot()
    def console_output(self) -> None:
        self.console.append(str(self.proc.readAllStandardOutput()))

    @pyqtSlot(QProcess.ProcessError)
    def cmd_error(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.Crashed:
            QMessageBox.critical(self.parent, 'Error calling an external process',
                                 self.proc.errorString(), buttons=QMessageBox.Close)

    @staticmethod
    def get_path(path: str) -> str:
        prefix = sys._MEIPASS if getattr(sys, 'frozen', False) else QFileInfo(__file__).absolutePath()
        return os.path.join(prefix, path)
