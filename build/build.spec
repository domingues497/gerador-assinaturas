# -*- mode: python ; coding: utf-8 -*-
# Spec do PyInstaller para o Gerador de Assinaturas.
# Gerar com: pyinstaller build/build.spec
import os

block_cipher = None
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPEC), ".."))

a = Analysis(
    [os.path.join(PROJECT_ROOT, "app.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        (os.path.join(PROJECT_ROOT, "templates"), "templates"),
        (os.path.join(PROJECT_ROOT, "static"), "static"),
    ],
    hiddenimports=["jinja2.ext", "jwt", "jwt.algorithms", "jwt.jwks_client"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="GeradorAssinaturas",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # --windowed: sem console visível
    onefile=True,
    icon=None,           # informe um .ico aqui se desejar um ícone customizado
)
