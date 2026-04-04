# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

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
] + collect_submodules('rich._unicode_data')


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

a_legacy = make_analysis('src/main.py')
pyz_legacy = PYZ(a_legacy.pure, a_legacy.zipped_data, cipher=block_cipher)
legacy_binaries = _filtered_binaries(a_legacy.binaries)

legacy_exe = EXE(
    pyz_legacy,
    a_legacy.scripts,
    legacy_binaries,
    a_legacy.datas,
    [],
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
