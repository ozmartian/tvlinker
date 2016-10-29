#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtCore import QSettings, Qt, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, qApp)


class Settings(QDialog):
    def __init__(self, parent, settings: QSettings, f=Qt.Tool):
        super(QDialog, self).__init__(parent, f)
        self.parent = parent
        self.settings = settings
        self.setLayout(self.init_form())
        self.update_dlmanager_form(self.dlmanager_comboBox.currentIndex())
        self.setWindowTitle('%s Settings' % qApp.applicationName())
        self.setWindowIcon(QIcon(self.parent.get_path('images/settings.png')))

    def init_form(self) -> QFormLayout:
        generalGroup = QGroupBox()
        general_formLayout = QFormLayout()
        self.sourceUrl_lineEdit = QLineEdit(self, text=self.settings.value('source_url'))
        self.sourceUrl_lineEdit.setFixedWidth(300)
        general_formLayout.addRow('Source URL:', self.sourceUrl_lineEdit)
        self.useragent_lineEdit = QLineEdit(self, text=self.settings.value('user_agent'))
        self.useragent_lineEdit.setFixedWidth(500)
        general_formLayout.addRow('User Agent:', self.useragent_lineEdit)
        self.dlpagecount_comboBox = QComboBox(self, toolTip='Default Page Count', editable=False,
                                         cursor=Qt.PointingHandCursor)
        self.dlpagecount_comboBox.setAutoFillBackground(True)
        self.dlpagecount_comboBox.setFixedWidth(50)
        self.dlpagecount_comboBox.addItems(('10', '20', '30', '40'))
        self.dlpagecount_comboBox.setCurrentIndex(self.dlpagecount_comboBox.findText(
            str(self.settings.value('dl_pagecount')), Qt.MatchFixedString))
        general_formLayout.addRow('Default Page Count:', self.dlpagecount_comboBox)
        generalGroup.setLayout(general_formLayout)

        debridGroup = QGroupBox()
        debrid_formLayout = QFormLayout()
        self.realdebridtoken_lineEdit = QLineEdit(self, text=self.settings.value('realdebrid_apitoken'))
        self.realdebridtoken_lineEdit.setFixedWidth(250)
        debrid_formLayout.addRow('real-debrid.com API Token:', self.realdebridtoken_lineEdit)
        debridGroup.setLayout(debrid_formLayout)

        dlmanagerGroup = QGroupBox()
        dlmanager_formLayout = QFormLayout()
        self.dlmanager_comboBox = QComboBox(self, editable=False, cursor=Qt.PointingHandCursor)
        self.dlmanager_comboBox.setAutoFillBackground(True)
        self.dlmanager_comboBox.setFixedWidth(85)
        self.dlmanager_comboBox.addItems(('built-in', 'aria2', 'pyLoad'))
        if sys.platform == 'win32':
            self.dlmanager_comboBox.addItem('IDM')
        self.dlmanager_comboBox.setCurrentIndex(self.dlmanager_comboBox.findText(
            str(self.settings.value('download_manager')), Qt.MatchFixedString))
        self.dlmanager_comboBox.currentIndexChanged.connect(self.update_dlmanager_form)
        dlmanager_formLayout.addRow('Download Manager:', self.dlmanager_comboBox)
        dlmanager_layout = QHBoxLayout()
        dlmanager_layout.addLayout(dlmanager_formLayout)
        self.dlmanager_logo = QLabel()
        self.dlmanager_logo.setAlignment(Qt.AlignCenter)
        self.dlmanager_logo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        dlmanager_layout.addWidget(self.dlmanager_logo)
        dlmanagerGroup.setLayout(dlmanager_layout)

        self.update_dlmanager_logo()

        self.dlmanagersettings_formLayout = QFormLayout()
        self.dlmanagersettingsGroup = QGroupBox()
        self.dlmanagersettingsGroup.setLayout(self.dlmanagersettings_formLayout)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)
        save_button = QPushButton(self, text='Save', clicked=self.save_settings)
        cancel_button = QPushButton(self, text='Cancel', clicked=self.close)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        formLayout = QFormLayout()
        formLayout.addWidget(generalGroup)
        formLayout.addWidget(debridGroup)
        formLayout.addRow(dlmanagerGroup)
        formLayout.addRow(self.dlmanagersettingsGroup)
        formLayout.addRow(button_layout)
        return formLayout

    def update_dlmanager_logo(self):
        self.dlmanager_logo.setPixmap(QPixmap(self.parent.get_path('images/%s.png'
                                                                   % self.dlmanager_comboBox.currentText().lower())))

    @pyqtSlot(int)
    def update_dlmanager_form(self, index: int) -> None:
        dlmanager = self.dlmanager_comboBox.itemText(index)
        self.clear_layout()
        if dlmanager == 'aria2':
            self.aria2rpchost_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_host'))
            self.aria2rpchost_lineEdit.setFixedWidth(350)
            self.aria2rpcport_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_port'))
            self.aria2rpcport_lineEdit.setFixedWidth(100)
            self.aria2rpcsecret_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_secret'))
            self.aria2rpcsecret_lineEdit.setFixedWidth(100)
            self.aria2rpcuser_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_username'))
            self.aria2rpcuser_lineEdit.setFixedWidth(150)
            self.aria2rpcpass_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_password'))
            self.aria2rpcpass_lineEdit.setFixedWidth(150)
            aria2rpchost_infotext = QLabel('(default: http://localhost)')
            aria2rpchost_infotext.setStyleSheet('font-style:italic;')
            aria2rpchost_layout = QHBoxLayout()
            aria2rpchost_layout.addWidget(self.aria2rpchost_lineEdit)
            aria2rpchost_layout.addWidget(aria2rpchost_infotext)
            aria2rpcport_infotext = QLabel('(default: 6800)')
            aria2rpcport_infotext.setStyleSheet('font-style:italic;')
            aria2rpcport_layout = QHBoxLayout()
            aria2rpcport_layout.addWidget(self.aria2rpcport_lineEdit)
            aria2rpcport_layout.addWidget(aria2rpcport_infotext)
            self.dlmanagersettings_formLayout.addRow('RPC Daemon Host:', aria2rpchost_layout)
            self.dlmanagersettings_formLayout.addRow('RPC Daemon Port:', aria2rpcport_layout)
            self.dlmanagersettings_formLayout.addRow('RPC Daemon Secret:', self.aria2rpcsecret_lineEdit)
            self.dlmanagersettings_formLayout.addRow('RPC Daemon Username:', self.aria2rpcuser_lineEdit)
            self.dlmanagersettings_formLayout.addRow('RPC Daemon Password:', self.aria2rpcpass_lineEdit)
        elif dlmanager == 'pyLoad':
            self.pyloadhost_lineEdit = QLineEdit(self, text=self.settings.value('pyload_host'))
            self.pyloadhost_lineEdit.setFixedWidth(350)
            self.pyloaduser_lineEdit = QLineEdit(self, text=self.settings.value('pyload_username'))
            self.pyloaduser_lineEdit.setFixedWidth(150)
            self.pyloadpass_lineEdit = QLineEdit(self, text=self.settings.value('pyload_password'))
            self.pyloadpass_lineEdit.setFixedWidth(150)
            pyloadhost_infotext = QLabel('(default: http://localhost:8000)')
            pyloadhost_infotext.setStyleSheet('font-style:italic;')
            pyloadhost_layout = QHBoxLayout()
            pyloadhost_layout.addWidget(self.pyloadhost_lineEdit)
            pyloadhost_layout.addWidget(pyloadhost_infotext)
            self.dlmanagersettings_formLayout.addRow('pyLoad Host:', pyloadhost_layout)
            self.dlmanagersettings_formLayout.addRow('pyLoad Username:', self.pyloaduser_lineEdit)
            self.dlmanagersettings_formLayout.addRow('pyLoad Password:', self.pyloadpass_lineEdit)
        elif dlmanager == 'IDM':
            self.idmexepath_lineEdit = QLineEdit(self, text=self.settings.value('idm_exe_path'))
            self.idmexepath_lineEdit.setFixedWidth(500)
            self.dlmanagersettings_formLayout.addRow('IDM Executable (EXE) Path:', self.idmexepath_lineEdit)
        elif dlmanager == 'built-in':
            directdl_label = QLabel('Built-in download option has no configurable settings')
            directdl_label.setStyleSheet('color:#333; font-weight:300;')
            directdl_label.setAlignment(Qt.AlignCenter)
            self.dlmanagersettings_formLayout.addWidget(directdl_label)
        qApp.processEvents()
        self.update_dlmanager_logo()
        self.adjustSize()

    def clear_layout(self, layout: QFormLayout = None) -> None:
        if layout is None:
            layout = self.dlmanagersettings_formLayout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    @pyqtSlot()
    def save_settings(self) -> None:
        self.settings.setValue('source_url', self.sourceUrl_lineEdit.text())
        self.settings.setValue('user_agent', self.useragent_lineEdit.text())
        self.settings.setValue('dl_pagecount', self.dlpagecount_comboBox.currentText())
        self.settings.setValue('realdebrid_apitoken', self.realdebridtoken_lineEdit.text())
        self.settings.setValue('download_manager', self.dlmanager_comboBox.currentText())
        if self.dlmanager_comboBox.currentText() == 'aria2':
            self.settings.setValue('aria2_rpc_host', self.aria2rpchost_lineEdit.text())
            self.settings.setValue('aria2_rpc_port', self.aria2rpcport_lineEdit.text())
            self.settings.setValue('aria2_rpc_secret', self.aria2rpcsecret_lineEdit.text())
            self.settings.setValue('aria2_rpc_username', self.aria2rpcuser_lineEdit.text())
            self.settings.setValue('aria2_rpc_password', self.aria2rpcpass_lineEdit.text())
        elif self.dlmanager_comboBox.currentText() == 'pyLoad':
            self.settings.setValue('pyload_host', self.pyloadhost_lineEdit.text())
            self.settings.setValue('pyload_username', self.pyloaduser_lineEdit.text())
            self.settings.setValue('pyload_password', self.pyloadpass_lineEdit.text())
        elif self.dlmanager_comboBox.currentText() == 'IDM':
            self.settings.setValue('idm_exe_path', self.idmexepath_lineEdit.text())
        self.parent.init_settings()
        self.close()
