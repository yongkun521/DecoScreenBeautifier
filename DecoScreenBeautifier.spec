# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
ICON_PATH = None

a = Analysis(
    ['src/main.py', 'src/main_gui.py'],
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
        'PySide6',
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

gui_exe = EXE(
    pyz,
    a.scripts[1],
    a.binaries,
    a.zipfiles,
    a.datas,
    name='DecoScreenBeautifier',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=ICON_PATH,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

legacy_exe = EXE(
    pyz,
    a.scripts[0],
    a.binaries,
    a.zipfiles,
    a.datas,
    name='DecoScreenBeautifier_legacy_terminal',
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
