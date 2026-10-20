"""Bake every preset, body and stem preview once, for bundling with the app."""
import os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PySide6.QtWidgets import QApplication
from native import preset,PRESET_COUNT
from library import LIBRARY,default_design
import thumbnails
from mesh import build
from model_cache import signature
app=QApplication.instance() or QApplication([])
# Baking needs no writable user cache and does not alter any saved pumpkins.
thumbnails.build_cached=build
out=ROOT/'assets/previews';out.mkdir(exist_ok=True)
items=[(preset(i),False) for i in range(PRESET_COUNT)]
for category,field,stem_only in [('bodies','body',False),('stems','stem',True)]:
    for feature in LIBRARY[category]:
        d=default_design();d[field]=feature['id'];items.append((d,stem_only))
for i,(design,stem_only) in enumerate(items):
    path=out/(signature(design,image=True,stem_only=stem_only)+'.png')
    if not path.exists():
        image=thumbnails.render(design,stem_only=stem_only)
        if not image.save(str(path),'PNG'):raise OSError('Cannot save '+str(path))
    print(f'Baked {i+1}/{len(items)}',flush=True)
