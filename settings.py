#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtCore import QSettings, Qt, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QIcon, QPixmap
from PyQt5.QtWidgets import (QComboBox, QDialog, QDialogButtonBox,
                             QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLayout,
                             QLineEdit, QSizePolicy, QStackedLayout, QTabWidget, QVBoxLayout, QWidget, qApp)


class Settings(QDialog):
    def __init__(self, parent, settings: QSettings, f=Qt.WindowCloseButtonHint):
        super(Settings, self).__init__(parent, f)
        self.parent = parent
        self.settings = settings
        self.setWindowModality(Qt.ApplicationModal)
        self.tab_general = GeneralTab(self.settings)
        self.tab_favorites = FavoritesTab(self.settings)
        tabs = QTabWidget()
        tabs.addTab(self.tab_general, 'General')
        tabs.addTab(self.tab_favorites, 'Favorites')
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.close)
        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetFixedSize)
        layout.addWidget(tabs)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

        self.setWindowTitle('%s Settings' % qApp.applicationName())
        self.setWindowIcon(QIcon(self.parent.get_path('images/settings.png')))

    def save_settings(self) -> None:
        self.tab_general.save()
        self.tab_favorites.save()
        self.parent.init_settings()
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.tab_general.deleteLater()
        self.tab_favorites.deleteLater()
        self.deleteLater()
        super(QDialog, self).closeEvent(event)


class GeneralTab(QWidget):
    def __init__(self, settings: QSettings):
        super(GeneralTab, self).__init__()
        self.settings = settings
        generalGroup = QGroupBox()
        general_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        self.sourceUrl_lineEdit = QLineEdit(self, text=self.settings.value('source_url'), readOnly=True)
        self.sourceUrl_lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.sourceUrl_lineEdit.setMinimumWidth(500)
        self.sourceUrl_lineEdit.setStyleSheet('background-color:#EAEAEA')
        general_formLayout.addRow('Source URL:', self.sourceUrl_lineEdit)
        self.useragent_lineEdit = QLineEdit(self, text=self.settings.value('user_agent'), readOnly=True)
        self.useragent_lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.useragent_lineEdit.setStyleSheet('background-color:#EAEAEA')
        general_formLayout.addRow('User Agent:', self.useragent_lineEdit)
        self.dlpagecount_comboBox = QComboBox(self, toolTip='Default Page Count', editable=False,
                                         cursor=Qt.PointingHandCursor)
        self.dlpagecount_comboBox.setAutoFillBackground(True)
        self.dlpagecount_comboBox.setFixedWidth(50)
        self.dlpagecount_comboBox.addItems(('10', '20', '30', '40', '50'))
        self.dlpagecount_comboBox.setCurrentIndex(self.dlpagecount_comboBox.findText(
            str(self.settings.value('dl_pagecount')), Qt.MatchFixedString))
        general_formLayout.addRow('Default Page Count:', self.dlpagecount_comboBox)
        generalGroup.setLayout(general_formLayout)

        realdebrid_apitoken_link = '''<tr>
                                        <td align="right">
                                            <a href="https://real-debrid.com/apitoken" title="https://real-debrid.com/apitoken" target="_blank">
                                                access your API token settings
                                            </a>
                                        </td>
                                    </tr>''' if len(self.settings.value('realdebrid_apitoken')) == 0 else ''
        realdebrid_label = QLabel(textFormat=Qt.RichText, alignment=Qt.AlignVCenter, openExternalLinks=True)
        realdebrid_label.setText('''<style>
                                           a {
                                               text-decoration: none;
                                               font-size: 8pt;
                                               font-weight: 500;
                                               color: #481953;
                                           }
                                       </style>
                                       <table border="0" cellspacing="0" cellpadding="3">
                                           <tr valign="middle" align="left">
                                              <td>
                                                  <img src=":assets/images/realdebrid.png" style="width:128px; height:26px;" />
                                               </td>
                                           </tr>
                                           %s
                                       </table>''' % realdebrid_apitoken_link)
        self.realdebridtoken_lineEdit = QLineEdit(self, text=self.settings.value('realdebrid_apitoken'), alignment=Qt.AlignVCenter)
        self.realdebridtoken_lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        realdebrid_formLayout = QFormLayout(labelAlignment=Qt.AlignRight, formAlignment=Qt.AlignVCenter)
        realdebrid_formLayout.addRow('API Token:', self.realdebridtoken_lineEdit)
        realdebrid_logoLayout = QHBoxLayout()
        realdebrid_logoLayout.addWidget(realdebrid_label)
        realdebrid_logoLayout.addLayout(realdebrid_formLayout)
        debridGroup = QGroupBox()
        debridGroup.setLayout(realdebrid_logoLayout)

        dlmanagerGroup = QGroupBox()
        dlmanager_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        dlmanager_formLayout.setAlignment(Qt.AlignVCenter)
        self.dlmanager_comboBox = QComboBox(self, editable=False, cursor=Qt.PointingHandCursor)
        self.dlmanager_comboBox.setAutoFillBackground(True)
        self.dlmanager_comboBox.setFixedWidth(85)
        self.dlmanager_comboBox.addItems(('built-in', 'aria2', 'pyLoad'))
        if sys.platform == 'win32':
            self.dlmanager_comboBox.addItem('IDM')
        self.dlmanager_comboBox.setCurrentIndex(self.dlmanager_comboBox.findText(
            str(self.settings.value('download_manager')), Qt.MatchFixedString))
        dlmanager_formLayout.addRow('Download Manager:', self.dlmanager_comboBox)
        dlmanager_layout = QHBoxLayout()
        dlmanager_layout.addLayout(dlmanager_formLayout)
        dlmanagerGroup.setLayout(dlmanager_layout)

        directdl_label = QLabel('No settings available for built-in downloader')
        directdl_label.setStyleSheet('font-weight:300; text-align:center;')
        directdl_label.setAlignment(Qt.AlignCenter)

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
        aria2rpchost_infotext = QLabel('default: http://localhost')
        aria2rpchost_infotext.setStyleSheet('font-weight:300;')
        aria2rpchost_layout = QHBoxLayout()
        aria2rpchost_layout.addWidget(self.aria2rpchost_lineEdit)
        aria2rpchost_layout.addWidget(aria2rpchost_infotext)
        aria2rpcport_infotext = QLabel('default: 6800')
        aria2rpcport_infotext.setStyleSheet('font-weight:300;')
        aria2rpcport_layout = QHBoxLayout()
        aria2rpcport_layout.addWidget(self.aria2rpcport_lineEdit)
        aria2rpcport_layout.addWidget(aria2rpcport_infotext)
        aria2_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        aria2_formLayout.addRow('RPC Daemon Host:', aria2rpchost_layout)
        aria2_formLayout.addRow('RPC Daemon Port:', aria2rpcport_layout)
        aria2_formLayout.addRow('RPC Daemon Secret:', self.aria2rpcsecret_lineEdit)
        aria2_formLayout.addRow('RPC Daemon Username:', self.aria2rpcuser_lineEdit)
        aria2_formLayout.addRow('RPC Daemon Password:', self.aria2rpcpass_lineEdit)
        aria2_settings = QWidget()
        aria2_settings.setLayout(aria2_formLayout)

        self.pyloadhost_lineEdit = QLineEdit(self, text=self.settings.value('pyload_host'))
        self.pyloadhost_lineEdit.setFixedWidth(350)
        self.pyloaduser_lineEdit = QLineEdit(self, text=self.settings.value('pyload_username'))
        self.pyloaduser_lineEdit.setFixedWidth(150)
        self.pyloadpass_lineEdit = QLineEdit(self, text=self.settings.value('pyload_password'))
        self.pyloadpass_lineEdit.setFixedWidth(150)
        pyloadhost_infotext = QLabel('default: http://localhost:8000')
        pyloadhost_infotext.setStyleSheet('font-weight:300;')
        pyloadhost_layout = QHBoxLayout()
        pyloadhost_layout.addWidget(self.pyloadhost_lineEdit)
        pyloadhost_layout.addWidget(pyloadhost_infotext)
        pyload_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        pyload_formLayout.addRow('pyLoad Host:', pyloadhost_layout)
        pyload_formLayout.addRow('pyLoad Username:', self.pyloaduser_lineEdit)
        pyload_formLayout.addRow('pyLoad Password:', self.pyloadpass_lineEdit)
        pyload_settings = QWidget()
        pyload_settings.setLayout(pyload_formLayout)

        self.idmexepath_lineEdit = QLineEdit(self, text=self.settings.value('idm_exe_path'))
        self.idmexepath_lineEdit.setFixedWidth(500)
        idm_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        idm_formLayout.addRow('IDM Executable (EXE) Path:', self.idmexepath_lineEdit)
        idm_settings = QWidget()
        idm_settings.setLayout(idm_formLayout)

        self.dlmanagersettings_layout = QStackedLayout()
        self.dlmanagersettings_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.dlmanagersettings_layout.addWidget(directdl_label)
        self.dlmanagersettings_layout.addWidget(aria2_settings)
        self.dlmanagersettings_layout.addWidget(pyload_settings)
        self.dlmanagersettings_layout.addWidget(idm_settings)
        self.dlmanagersettings_layout.setCurrentIndex(self.dlmanager_comboBox.currentIndex())

        self.dlmanager_comboBox.currentIndexChanged.connect(self.dlmanagersettings_layout.setCurrentIndex)

        dlmanagersettingsGroup = QGroupBox()
        dlmanagersettingsGroup.setLayout(self.dlmanagersettings_layout)

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(generalGroup)
        tab_layout.addWidget(debridGroup)
        tab_layout.addWidget(dlmanagerGroup)
        tab_layout.addWidget(dlmanagersettingsGroup)

        self.setLayout(tab_layout)

    def save(self) -> None:
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


class FavoritesTab(QWidget):
    def __init__(self, settings: QSettings):
        super(FavoritesTab, self).__init__()
        self.settings = settings
        faves_content = QLabel(pixmap=QPixmap(':assets/images/comingsoon.png'), alignment=Qt.AlignCenter)
        faves_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        faves_layout = QVBoxLayout()
        faves_layout.addWidget(faves_content)
        self.setLayout(faves_layout)
        pass

    def save(self) -> None:
        pass
