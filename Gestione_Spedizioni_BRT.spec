# -*- mode: python ; coding: utf-8 -*-

import sys
import os

a = Analysis(
    ['brt_app_pyqt5.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('github_token.txt', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', '_pytest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Determine icon based on platform
if sys.platform == 'darwin':
    icon_file = 'assets/igea_icon.icns'
elif sys.platform == 'win32':
    # Check if .ico file exists, otherwise use None
    icon_file = 'assets/igea_icon.ico' if os.path.exists('assets/igea_icon.ico') else None
else:
    icon_file = None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Gestione_Spedizioni_BRT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Gestione_Spedizioni_BRT',
)
# BUNDLE is only for macOS
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Gestione_Spedizioni_BRT.app',
        icon='assets/igea_icon.icns',
        bundle_identifier=None,
    )
