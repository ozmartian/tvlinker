#!/usr/bin/env python3
# -*- mode: python -*-

import os
import sys

import PyQt5
import qtawesome

block_cipher = None


a = Analysis(['../tvlinker.py'],
             pathex=[
                 os.path.join(sys.modules['PyQt5'].__path__[0], 'Qt', 'bin'),
                 '..'
             ],
             binaries=[],
             datas=[
                 ('../tvlinker.ini', '.'),
                 ('../__init__.py', '.'),
                 (os.path.join(sys.modules['qtawesome'].__path__[0], 'fonts', '*'), './qtawesome/fonts')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='TVLinker',
          debug=False,
          strip=True,
          upx=True,
          console=False , icon='../data/icons/tvlinker.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=True,
               upx=True,
               name='TVLinker')
app = BUNDLE(coll,
             name='TVLinker.app',
             icon='../data/icons/tvlinker.icns',
             bundle_identifier='com.ozmartians.tvlinker')
