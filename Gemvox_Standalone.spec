# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('gemvox/accessibility/lib/*.dll', 'gemvox/accessibility/lib'),
    ('gemvox/accessibility/lib/nvdaControllerClient32.dll', '.'),
    ('gemvox/accessibility/lib/nvdaControllerClient64.dll', '.'),
]
datas += collect_data_files('_sounddevice_data')
datas += collect_data_files('sounddevice')
datas += collect_data_files('google.genai')

hiddenimports = [
    'wx',
    'sounddevice',
    '_sounddevice_data',
    'win32com',
    'win32com.client',
    'pythoncom',
    'dotenv',
    'websockets',
    'pydantic',
    'pydantic_core',
    'cryptography',
]
hiddenimports += [m for m in collect_submodules('google.genai') if not m.startswith('google.genai.tests')]
hiddenimports += collect_submodules('gemvox')

a = Analysis(
    ['gemvox.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'tests', 'google.genai.tests'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Gemvox_Standalone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
)
