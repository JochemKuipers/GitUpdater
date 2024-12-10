# main.spec
block_cipher = None

added_files = [
    ('components/*.ui', 'components'),  # UI files
    ('assets/*', 'assets'),  # Assets/resources
    ('src/*', 'src'),  # Source files
    ('requirements.txt', '.'), # Requirements file
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('components/*.ui', 'components'),
        ('assets/*', 'assets'), 
        ('src/config_template.json', 'src'),
        ('requirements.txt', '.'),
        ('.env', '.')
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.uic',
        'dotenv',
        'PyQt6.QtWaylandClient'  # Remove XCB, keep Wayland
    ],
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,        # Include binaries
    a.zipfiles,        # Include zipfiles
    a.datas,           # Include data files
    [],
    name='GitUpdater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,  # Runtime files in temp
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/giticon.ico',
    onefile=True       # Create single file
)