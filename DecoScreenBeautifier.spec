# -*- mode: python ; coding: utf-8 -*-

import importlib.util
from pathlib import Path

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


def _pyside6_package_dir() -> Path | None:
    spec = importlib.util.find_spec('PySide6')
    origin = getattr(spec, 'origin', None)
    if not origin:
        return None
    package_dir = Path(origin).resolve().parent
    return package_dir if package_dir.is_dir() else None


def _filtered_binaries(binaries):
    runtime_names = {
        'vcruntime140.dll',
        'vcruntime140_1.dll',
        'msvcp140.dll',
        'msvcp140_1.dll',
        'msvcp140_2.dll',
        'concrt140.dll',
        'ucrtbase.dll',
    }

    def _is_conda_source(path: str) -> bool:
        normalized = str(path).replace('/', '\\').lower()
        return (
            '\\anaconda3\\' in normalized
            or '\\miniconda' in normalized
            or '\\mambaforge' in normalized
            or '\\conda\\envs\\' in normalized
        )

    filtered = []
    for dest, src, kind in binaries:
        dest_norm = str(dest).replace('\\', '/')
        file_name = Path(dest_norm).name.lower()
        is_root_binary = '/' not in dest_norm

        if _is_conda_source(src):
            continue

        if file_name.startswith('api-ms-win-') or file_name.startswith('ext-ms-win-'):
            continue

        if is_root_binary:
            if file_name in runtime_names:
                continue
            if file_name.startswith('icu') and file_name.endswith('.dll'):
                continue
        filtered.append((dest, src, kind))

    pyside6_dir = _pyside6_package_dir()
    if pyside6_dir is not None:
        for dll_name in (
            'VCRUNTIME140.dll',
            'VCRUNTIME140_1.dll',
            'MSVCP140.dll',
            'MSVCP140_1.dll',
            'MSVCP140_2.dll',
            'concrt140.dll',
        ):
            candidate = pyside6_dir / dll_name
            if candidate.is_file():
                filtered.append((dll_name, str(candidate), 'BINARY'))
    return filtered


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
gui_binaries = _filtered_binaries(a_gui.binaries)

gui_exe = EXE(
    pyz_gui,
    a_gui.scripts,
    gui_binaries,
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
legacy_binaries = _filtered_binaries(a_legacy.binaries)

legacy_exe = EXE(
    pyz_legacy,
    a_legacy.scripts,
    legacy_binaries,
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
