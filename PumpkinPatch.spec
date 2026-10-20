# Native build. Run pyinstaller PumpkinPatch.spec on the target operating system.
from pathlib import Path
import sys
root=Path(SPECPATH)
datas=[(str(root/'assets/fonts'),'assets/fonts'),(str(root/'assets/icons'),'assets/icons')]
datas += [(str(root/'assets/previews'),'assets/previews')]
datas += [(str(p),'assets') for p in (root/'assets').glob('*.json.gz')]
a=Analysis([str(root/'main.py')],pathex=[str(root)],binaries=[],datas=datas,
    hiddenimports=['OpenGL.platform.darwin' if sys.platform=='darwin' else 'OpenGL.platform.win32' if sys.platform=='win32' else 'OpenGL.platform.glx','OpenGL.arrays.numpymodule'],
    excludes=['tkinter','webview','PyQt5','PyQt6','PySide2','PySide6.QtQml','PySide6.QtQuick','PySide6.QtNetwork','PySide6.QtWebEngineCore','PIL','pytest','unittest','IPython','matplotlib'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],icon=str(root/'assets/icons/pumpkin-patch.ico') if sys.platform=='win32' else None,exclude_binaries=True,name='Pumpkin Patch',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False,target_arch='arm64' if sys.platform=='darwin' else None,codesign_identity=None,entitlements_file=None)
if sys.platform=='darwin':
    app=BUNDLE(exe,a.binaries,a.datas,name='Pumpkin Patch.app',icon=str(root/'assets/icons/pumpkin-patch-3d.icns'),bundle_identifier='local.pumpkinpatch.creator',info_plist={'NSHighResolutionCapable':True,'CFBundleShortVersionString':'1.0.0'})
else:
    coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='Pumpkin Patch')
