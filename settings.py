#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import qtawesome as qta
from PyQt5.QtCore import QSettings, Qt, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QKeyEvent, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
                             QStackedLayout, QStyleFactory, QTabWidget, QVBoxLayout, QWidget, qApp)


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
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.close)
        layout = QVBoxLayout()
        layout.addWidget(tabs)
        layout.addWidget(button_box)
        self.setLayout(layout)
        self.setWindowTitle('%s Settings' % qApp.applicationName())
        self.setWindowIcon(self.parent.icon_settings)

    def save_settings(self) -> None:
        self.tab_general.save()
        self.tab_favorites.save()
        self.parent.init_settings()
        if self.settings.value('ui_style').lower() != QApplication.style().objectName().lower():
            QApplication.setStyle(QStyleFactory.create(self.settings.value('ui_style')))
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            return
        super(Settings, self).keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.tab_general.deleteLater()
        self.tab_favorites.deleteLater()
        self.deleteLater()
        event.accept()


class GeneralTab(QWidget):
    def __init__(self, settings: QSettings):
        super(GeneralTab, self).__init__()
        self.settings = settings

        realdebrid_logo = QLabel(pixmap=QPixmap(':assets/images/realdebrid.png'))
        self.realdebridtoken_lineEdit = QLineEdit(self, text=self.settings.value('realdebrid_apitoken'))
        self.realdebridtoken_lineEdit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.realdebridtoken_lineEdit.setMinimumWidth(250)
        apitoken_link = '<a href="https://real-debrid.com/apitoken" title="https://real-debrid.com/apitoken" ' \
                        'target="_blank">get your API token here</a>'
        realdebrid_apitoken_link = QLabel(text=apitoken_link, textFormat=Qt.RichText, openExternalLinks=True)
        realdebrid_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        realdebrid_formLayout.addRow('API Token:', self.realdebridtoken_lineEdit)
        if not len(self.settings.value('realdebrid_apitoken')):
            realdebrid_formLayout.addRow('', realdebrid_apitoken_link)
        realdebrid_layout = QHBoxLayout()
        realdebrid_layout.addWidget(realdebrid_logo)
        realdebrid_layout.addSpacing(15)
        realdebrid_layout.addLayout(realdebrid_formLayout)
        realdebrid_group = QGroupBox()
        realdebrid_group.setLayout(realdebrid_layout)

        self.dlmanager_comboBox = QComboBox(self, editable=False, cursor=Qt.PointingHandCursor)
        self.dlmanager_comboBox.setAutoFillBackground(True)
        self.dlmanager_comboBox.addItems(('built-in', 'aria2', 'pyLoad'))
        if sys.platform == 'win32':
            self.dlmanager_comboBox.addItem('IDM')
        if sys.platform.startswith('linux'):
            self.dlmanager_comboBox.addItem('kget')
        self.dlmanager_comboBox.setCurrentIndex(self.dlmanager_comboBox.findText(
            str(self.settings.value('download_manager')), Qt.MatchFixedString))

        self.updater_freq_comboBox = QComboBox(self, toolTip='Automatically check for application updates',
                                               editable=False, cursor=Qt.PointingHandCursor)
        self.updater_freq_comboBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.updater_freq_comboBox.addItems(('Never', 'Daily', 'Weekly', 'Monthly'))
        self.updater_freq_comboBox.insertSeparator(1)
        self.updater_freq_comboBox.setCurrentIndex(self.updater_freq_comboBox.findText(
            str(self.settings.value('updater_freq', 'Never')), Qt.MatchFixedString))
        self.dlpagecount_comboBox = QComboBox(self, toolTip='Default Page Count', editable=False,
                                              cursor=Qt.PointingHandCursor)
        self.dlpagecount_comboBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.dlpagecount_comboBox.addItems(('10', '20', '30', '40', '50'))
        self.dlpagecount_comboBox.setCurrentIndex(self.dlpagecount_comboBox.findText(
            str(self.settings.value('dl_pagecount')), Qt.MatchFixedString))
        self.uistyle_comboBox = QComboBox(self, toolTip='UI Style', editable=False, cursor=Qt.PointingHandCursor)
        self.uistyle_comboBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.uistyle_comboBox.setMinimumContentsLength(len(max(QStyleFactory.keys(), key=len)))
        self.uistyle_comboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.uistyle_comboBox.addItems(QStyleFactory.keys())
        self.uistyle_comboBox.setCurrentIndex(
            self.uistyle_comboBox.findText(str(self.settings.value('ui_style')), Qt.MatchFixedString))

        field_width = self.uistyle_comboBox.minimumContentsLength()
        self.dlpagecount_comboBox.setMinimumContentsLength(field_width)
        self.dlmanager_comboBox.setMinimumContentsLength(field_width)
        self.updater_freq_comboBox.setMinimumContentsLength(field_width)

        general_formlayout_left = QFormLayout(labelAlignment=Qt.AlignRight)
        general_formlayout_left.addRow('Default Page Count:', self.dlpagecount_comboBox)
        general_formlayout_left.addRow('Download Manager:', self.dlmanager_comboBox)
        general_formlayout_right = QFormLayout(labelAlignment=Qt.AlignRight)
        general_formlayout_right.addRow('Check for Updates:', self.updater_freq_comboBox)
        general_formlayout_right.addRow('UI Style:', self.uistyle_comboBox)
        general_formlayout = QHBoxLayout()
        general_formlayout.addStretch(1)
        general_formlayout.addLayout(general_formlayout_left)
        general_formlayout.addStretch(1)
        general_formlayout.addLayout(general_formlayout_right)
        general_formlayout.addStretch(1)
        general_group = QGroupBox()
        general_group.setLayout(general_formlayout)

        directdl_label = QLabel('No settings for built-in downloader')
        directdl_label.setStyleSheet('font-weight:300; text-align:center;')
        directdl_label.setAlignment(Qt.AlignCenter)

        self.aria2rpchost_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_host'))
        self.aria2rpchost_lineEdit.setPlaceholderText('http://localhost')
        self.aria2rpchost_lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.aria2rpcport_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_port'))
        self.aria2rpcport_lineEdit.setPlaceholderText('6800')
        self.aria2rpcport_lineEdit.setFixedWidth(100)
        self.aria2rpcsecret_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_secret'))
        self.aria2rpcsecret_lineEdit.setFixedWidth(100)
        self.aria2rpcuser_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_username'))
        self.aria2rpcuser_lineEdit.setFixedWidth(150)
        self.aria2rpcpass_lineEdit = QLineEdit(self, text=self.settings.value('aria2_rpc_password'))
        self.aria2rpcpass_lineEdit.setFixedWidth(150)
        aria2_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        aria2_formLayout.addRow('RPC Host:', self.aria2rpchost_lineEdit)
        aria2_formLayout_left = QFormLayout(labelAlignment=Qt.AlignRight)
        aria2_formLayout_left.addRow('RPC Port:', self.aria2rpcport_lineEdit)
        aria2_formLayout_left.addRow('RPC Secret:', self.aria2rpcsecret_lineEdit)
        aria2_formLayout_right = QFormLayout(labelAlignment=Qt.AlignRight)
        aria2_formLayout_right.addRow('RPC Username:', self.aria2rpcuser_lineEdit)
        aria2_formLayout_right.addRow('RPC Password:', self.aria2rpcpass_lineEdit)
        aria2_formLayout_hbox = QHBoxLayout()
        aria2_formLayout_hbox.addStretch(1)
        aria2_formLayout_hbox.addLayout(aria2_formLayout_left)
        aria2_formLayout_hbox.addStretch(1)
        aria2_formLayout_hbox.addLayout(aria2_formLayout_right)
        aria2_formLayout_hbox.addStretch(1)
        aria2_formLayout.addRow(aria2_formLayout_hbox)
        aria2_settings = QWidget()
        aria2_settings.setLayout(aria2_formLayout)

        self.pyloadhost_lineEdit = QLineEdit(self, text=self.settings.value('pyload_host'))
        self.pyloadhost_lineEdit.setPlaceholderText('http://localhost:8000')
        self.pyloadhost_lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.pyloaduser_lineEdit = QLineEdit(self, text=self.settings.value('pyload_username'))
        self.pyloaduser_lineEdit.setFixedWidth(200)
        self.pyloadpass_lineEdit = QLineEdit(self, text=self.settings.value('pyload_password'))
        self.pyloadpass_lineEdit.setFixedWidth(200)
        pyload_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        pyload_formLayout.addRow('pyLoad Host:', self.pyloadhost_lineEdit)
        pyload_formLayout.addRow('pyLoad Username:', self.pyloaduser_lineEdit)
        pyload_formLayout.addRow('pyLoad Password:', self.pyloadpass_lineEdit)
        pyload_settings = QWidget()
        pyload_settings.setLayout(pyload_formLayout)

        if sys.platform == 'win32':
            self.idmexepath_lineEdit = QLineEdit(self, text=self.settings.value('idm_exe_path'))
            self.idmexepath_lineEdit.setPlaceholderText('C:\Program Files (x86)\Internet Download Manager\IDMan.exe')
            self.idmexepath_lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            idm_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
            idm_formLayout.addRow('IDM EXE Path:', self.idmexepath_lineEdit)
            idm_settings = QWidget()
            idm_settings.setLayout(idm_formLayout)

        if sys.platform.startswith('linux'):
            self.kgetpath_lineEdit = QLineEdit(self, text=self.settings.value('kget_path'))
            self.kgetpath_lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            kget_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
            kget_formLayout.addRow('kget Path:', self.kgetpath_lineEdit)
            kget_settings = QWidget()
            kget_settings.setLayout(kget_formLayout)

        self.dlmanagersettings_layout = QStackedLayout()
        self.dlmanagersettings_layout.addWidget(directdl_label)
        self.dlmanagersettings_layout.addWidget(aria2_settings)
        self.dlmanagersettings_layout.addWidget(pyload_settings)
        if sys.platform == 'win32':
            self.dlmanagersettings_layout.addWidget(idm_settings)
        if sys.platform.startswith('linux'):
            self.dlmanagersettings_layout.addWidget(kget_settings)

        self.dlmanagersettings_layout.setCurrentIndex(self.dlmanager_comboBox.currentIndex())
        self.dlmanager_comboBox.currentIndexChanged.connect(self.dlmanagersettings_layout.setCurrentIndex)
        dlmanagersettings_group = QGroupBox()
        dlmanagersettings_group.setLayout(self.dlmanagersettings_layout)

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(realdebrid_group)
        tab_layout.addWidget(general_group)
        tab_layout.addWidget(dlmanagersettings_group)

        self.setLayout(tab_layout)

    def save(self) -> None:
        self.settings.setValue('updater_freq', self.updater_freq_comboBox.currentText())
        self.settings.setValue('dl_pagecount', self.dlpagecount_comboBox.currentText())
        self.settings.setValue('ui_style', self.uistyle_comboBox.currentText())
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
        elif self.dlmanager_comboBox.currentText() == 'kget':
            self.settings.setValue('kget_path', self.kgetpath_lineEdit.text())


class FavoritesTab(QWidget):
    def __init__(self, settings: QSettings):
        super(FavoritesTab, self).__init__()
        self.settings = settings
        faves_formLayout = QFormLayout(labelAlignment=Qt.AlignRight)
        self.faves_lineEdit = QLineEdit(self)
        self.faves_lineEdit.returnPressed.connect(self.add_item)
        self.faves_lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        faves_addItemButton = QPushButton(parent=self, flat=False, cursor=Qt.PointingHandCursor, text='Add',
                                          icon=qta.icon('fa.plus', color='#555'), toolTip='Add item',
                                          clicked=self.add_item)
        faves_deleteItemButton = QPushButton(parent=self, flat=False, cursor=Qt.PointingHandCursor, text='Delete',
                                             icon=qta.icon('fa.minus', color='#555'), toolTip='Delete selected item',
                                             clicked=self.delete_items)
        faves_buttonLayout = QHBoxLayout()
        faves_buttonLayout.addWidget(faves_addItemButton)
        faves_buttonLayout.addWidget(faves_deleteItemButton)
        faves_formLayout.addRow('Item Label:', self.faves_lineEdit)
        faves_formLayout.addRow(faves_buttonLayout)
        faves_formLayout.addRow(self.get_notes())
        self.faves_listWidget = QListWidget(self)
        self.faves_listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.faves_listWidget.setSortingEnabled(True)
        self.add_items(self.settings.value('favorites', ''))

        tab_layout = QHBoxLayout()
        tab_layout.addLayout(faves_formLayout)
        tab_layout.addWidget(self.faves_listWidget)

        self.setLayout(tab_layout)

    def add_items(self, items: list) -> None:
        for item in items:
            listitem = QListWidgetItem(item, self.faves_listWidget)
            listitem.setFlags(listitem.flags() | Qt.ItemIsEditable)
        self.faves_listWidget.sortItems(Qt.AscendingOrder)

    @pyqtSlot()
    def delete_items(self) -> None:
        for item in self.faves_listWidget.selectedItems():
            deleted_item = self.faves_listWidget.takeItem(self.faves_listWidget.row(item))
            del deleted_item

    @pyqtSlot()
    def add_item(self) -> None:
        if len(self.faves_lineEdit.text()):
            item = QListWidgetItem(self.faves_lineEdit.text(), self.faves_listWidget)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.faves_listWidget.sortItems(order=Qt.AscendingOrder)
            self.faves_lineEdit.clear()

    def get_notes(self) -> QLabel:
        content = QLabel()
        content.setStyleSheet('margin:10px; border:1px solid #BABABA; padding:10px; color:#666;')
        content.setTextFormat(Qt.RichText)
        content.setWordWrap(True)
        content.setText('''Labels from this list will be used to filter links. Filtering is NOT case-sensitive.
                            <br/><br/>Example:<br/><br/>&nbsp;&nbsp;&nbsp;&nbsp;the simpsons<br/>
                            &nbsp;&nbsp;&nbsp;&nbsp;south park''')
        return content

    def save(self) -> None:
        if self.faves_listWidget.count():
            faves = []
            for row in range(0, self.faves_listWidget.count()):
                faves.append(self.faves_listWidget.item(row).text())
            self.settings.setValue('favorites', faves)
