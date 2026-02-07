# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
ICON_PATH = None

COMMON_PATHEX = []
COMMON_BINARIES = []
COMMON_DATAS = [
    ('src/ui/styles.tcss', 'ui'),
    ('assets', 'assets'),
]
COMMON_HIDDENIMPORTS = [
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
]


def make_analysis(entry_script):
    return Analysis(
        [entry_script],
        pathex=COMMON_PATHEX,
        binaries=COMMON_BINARIES,
        datas=COMMON_DATAS,
        hiddenimports=COMMON_HIDDENIMPORTS,
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
    )

a_gui = make_analysis('src/main_gui.py')
pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=block_cipher)

gui_exe = EXE(
    pyz_gui,
    a_gui.scripts,
    a_gui.binaries,
    a_gui.datas,
    [],
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

a_legacy = make_analysis('src/main.py')
pyz_legacy = PYZ(a_legacy.pure, a_legacy.zipped_data, cipher=block_cipher)

legacy_exe = EXE(
    pyz_legacy,
    a_legacy.scripts,
    a_legacy.binaries,
    a_legacy.datas,
    [],
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
