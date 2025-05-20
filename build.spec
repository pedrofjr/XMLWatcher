# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# Caminho absoluto para o ícone
icon_path = os.path.abspath(os.path.join('src', 'resources', 'icone.ico'))

a = Analysis(
    ['src/main.py'],
    pathex=['.', './src'],
    binaries=[],
    datas=[('src/resources/icone.ico', 'resources')],  # Inclui apenas o arquivo do ícone
    hiddenimports=[
        'lxml._elementpath',
        'lxml.etree',
        'watchdog.observers.winapi',
        'watchdog.observers.polling',
        'src.gui',
        'src.utils',
        'src.watcher'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='XMLWatcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path  # Usa o caminho absoluto do ícone
)
