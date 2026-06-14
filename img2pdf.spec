# img2pdf.spec
# Use: pyinstaller img2pdf.spec
import sys
import os

block_cipher = None

a = Analysis(
    ['img2pdf.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PIL', 'PIL.Image', 'PIL.ImageTk',
        'PIL.PngImagePlugin', 'PIL.JpegImagePlugin',
        'PIL.BmpImagePlugin', 'PIL.GifImagePlugin',
        'PIL.TiffImagePlugin', 'PIL.WebPImagePlugin',
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'scipy', 'matplotlib', 'pandas'],
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
    name='Img2PdfZ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # sem janela de console (GUI only)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',      # descomente e forneça icon.ico para ícone personalizado
)
