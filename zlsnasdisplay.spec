# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Get the project root directory
project_root = Path.cwd()
fonts_dir = project_root / 'zlsnasdisplay' / 'fonts'

a = Analysis(
    ['zlsnasdisplay/__main__.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include font files
        (str(fonts_dir / 'Ubuntu-Regular.ttf'), 'zlsnasdisplay/fonts'),
        (str(fonts_dir / 'Ubuntu-Light.ttf'), 'zlsnasdisplay/fonts'),
        (str(fonts_dir / 'MaterialSymbolsRounded.ttf'), 'zlsnasdisplay/fonts'),
    ],
    hiddenimports=[
        # Core modules
        'zlsnasdisplay.main',
        'zlsnasdisplay.display_controller',
        'zlsnasdisplay.display_renderer',
        'zlsnasdisplay.system_operations',
        'zlsnasdisplay.network_operations',
        'zlsnasdisplay.config',
        'zlsnasdisplay.display_config',
        # Waveshare driver
        'zlsnasdisplay.waveshare_epd',
        'zlsnasdisplay.waveshare_epd.epd2in9_V2',
        'zlsnasdisplay.waveshare_epd.epdconfig',
        # Hardware dependencies (may not be present in all environments)
        'gpiozero',
        'gpiozero.pins',
        'gpiozero.pins.lgpio',
        'gpiozero.pins.rpigpio',
        'gpiozero.pins.pigpio',
        'gpiozero.pins.native',
        'lgpio',
        'spidev',
        # PIL/Pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        # System monitoring
        'psutil',
        # Scheduling
        'schedule',
        # Network
        'requests',
        # Web dashboard (optional)
        'fastapi',
        'uvicorn',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        # Matter integration (optional)
        'zlsnasdisplay.matter_device',
        'circuitmatter',
        'qrcode',
        'qrcode.image.pil',
        'cryptography',
        # Debian package management (may not be present)
        'apt',
        'apt.progress',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        'tests',
        'pytest',
        'unittest',
        # Exclude dev tools
        'mypy',
        'ruff',
        'pre_commit',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='zlsnasdisplay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
