# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('baseline_processes.json', '.'), ('config/json/agents_config.json', 'config/json')],
    hiddenimports=['langchain', 'langchain.schema', 'crewai', 'crewai.agents', 'crewai.tasks', 'crewai.crew', 'crewai.tools', 'tools', 'tools.security_tools', 'agents', 'agents.security_agents', 'agents.tasks', 'agents.crew', 'models', 'models.llm_setup', 'config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PyQt6', 'PySide6', 'PyQt5', 'PySide2', 'PyQt4', 'PySide', 'qt', 'Qt', 'tkinter', 'IPython', 'scipy'],
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
    name='AI-Agent应急响应系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
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
