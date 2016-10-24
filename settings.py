#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, qApp)


class Settings(QDialog):
    def __init__(self, parent, settings, f=Qt.Tool):
        super(QDialog, self).__init__(parent, f)
        self.parent = parent
        self.settings = settings
        self.setLayout(self.init_form())
        self.setWindowTitle('%s Settings' % qApp.applicationName())

    def init_form(self) -> QFormLayout:
        generalGroup = QGroupBox('General')
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

        debridGroup = QGroupBox('Debrid')
        debrid_formLayout = QFormLayout()
        self.realdebridtoken_lineEdit = QLineEdit(self, text=self.settings.value('realdebrid_apitoken'))
        self.realdebridtoken_lineEdit.setFixedWidth(250)
        debrid_formLayout.addRow('real-debrid.com API Token:', self.realdebridtoken_lineEdit)
        debridGroup.setLayout(debrid_formLayout)

        dlmanager_formLayout = QFormLayout()
        self.dlmanager_comboBox = QComboBox(self, toolTip='Download Manager', editable=False,
                                            cursor=Qt.PointingHandCursor)
        self.dlmanager_comboBox.setAutoFillBackground(True)
        self.dlmanager_comboBox.setFixedWidth(85)
        self.dlmanager_comboBox.addItems(('direct', 'aria2', 'pyLoad', 'IDM'))
        self.dlmanager_comboBox.setCurrentIndex(self.dlmanager_comboBox.findText(
            str(self.settings.value('download_manager')), Qt.MatchFixedString))
        dlmanager_formLayout.addRow('Download Manager:', self.dlmanager_comboBox)
        self.aria2rpchost_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_host'))
        self.aria2rpchost_lineEdit.setFixedWidth(200)
        aria2rpchost_infotext = QLabel('(default: http://localhost)')
        aria2rpchost_infotext.setStyleSheet('font-style:italic;')
        aria2rpchost_layout = QHBoxLayout()
        aria2rpchost_layout.addWidget(self.aria2rpchost_lineEdit)
        aria2rpchost_layout.addWidget(aria2rpchost_infotext)
        dlmanager_formLayout.addRow('RPC Daemon Host:', aria2rpchost_layout)
        self.aria2rpcport_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_port'))
        self.aria2rpcport_lineEdit.setFixedWidth(85)
        aria2rpcport_infotext = QLabel('(default: 6800)')
        aria2rpcport_infotext.setStyleSheet('font-style:italic;')
        aria2rpcport_layout = QHBoxLayout()
        aria2rpcport_layout.addWidget(self.aria2rpcport_lineEdit)
        aria2rpcport_layout.addWidget(aria2rpcport_infotext)
        dlmanager_formLayout.addRow('RPC Daemon Port:', aria2rpcport_layout)
        self.aria2rpcsecret_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_secret'))
        self.aria2rpcsecret_lineEdit.setFixedWidth(100)
        dlmanager_formLayout.addRow('RPC Daemon Secret:', self.aria2rpcsecret_lineEdit)
        self.aria2rpcuser_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_username'))
        self.aria2rpcuser_lineEdit.setFixedWidth(150)
        dlmanager_formLayout.addRow('RPC Daemon Username:', self.aria2rpcuser_lineEdit)
        self.aria2rpcpass_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_password'))
        self.aria2rpcpass_lineEdit.setFixedWidth(150)
        dlmanager_formLayout.addRow('RPC Daemon Password:', self.aria2rpcpass_lineEdit)

        dlmanagerGroup = QGroupBox('Download Manager')
        dlmanagerGroup.setLayout(dlmanager_formLayout)

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
        formLayout.addRow(button_layout)
        return formLayout

    @pyqtSlot()
    def save_settings(self) -> None:
        pass
