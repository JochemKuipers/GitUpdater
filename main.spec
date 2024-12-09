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
        ('.env', '.')  # Include .env file
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.uic',
        'dotenv',
        'PyQt6.QtWaylandClient',
        'PyQt6.QtXcbQpa'
    ],
    noarchive=False
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GitUpdater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/giticon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GitUpdater'
)