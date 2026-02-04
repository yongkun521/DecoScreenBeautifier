# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
ICON_PATH = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/ui/styles.tcss', 'ui'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'textual.widgets',
        'textual.containers',
        'rich.progress',
        'rich.panel',
        'rich.align',
        'rich.layout',
        'PIL',
        'cv2',
        'numpy',
        'pyaudio',
        'psutil',
        'json5',
        'appdirs',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    name='DecoScreenBeautifier',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=ICON_PATH,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
