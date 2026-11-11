# -*- mode: python ; coding: utf-8 -*-
"""Especificação do PyInstaller para gerar o executável do ToschiBook.

Empacota o launcher (iniciar.py) junto com todos os recursos estáticos
(html, css, javascript) e o banco inicial. Gere com:

    pyinstaller ToschiBook.spec
"""

block_cipher = None

# Recursos que devem ir junto no executável.
datas = [
    ("html", "html"),
    ("css", "css"),
    ("javascript", "javascript"),
    ("uploads", "uploads"),
]

a = Analysis(
    ["iniciar.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "app",
        "routes",
        "models",
        "auth",
        "ativacao",
        "licenca",
        "database",
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
    [],
    name="ToschiBook",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # mantém o terminal (fecha = encerra o servidor)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="html/favicon.ico",
)
