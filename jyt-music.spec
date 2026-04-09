# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Collect assets and UI files
# (Source Path, Destination Folder in Bundle)
added_files = [
    ('src/assets/*', 'assets'),
    ('src/ui/style.qss', 'ui'),
]

# Check for bin folder (FFmpeg)
# If it's not present during build, PyInstaller will just skip it
# and the app will fall back to system PATH
if os.path.exists('src/bin'):
    print("Found src/bin, bundling FFmpeg binaries...")
    added_files.append(('src/bin/*', 'bin'))
else:
    print("src/bin not found, FFmpeg will not be bundled.")

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='jYT-Music',
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
    icon='src/assets/logo.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='jYT-Music-Desktop',
)
