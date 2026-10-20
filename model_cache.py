"""Persistent content-addressed geometry cache; labels never rebuild a mesh."""
import copy,gzip,hashlib,json,shutil,zlib
from collections import OrderedDict
from pathlib import Path
from legacy_mesh import Part
from mesh import build
from storage import DATA
VERSION='pumpkin-geometry-4'
_memory=OrderedDict()

def signature(design,*,image=False,stem_only=False):
    fields=('body','stem','lid','cuts','parts')+ (('color','lit') if image else ())
    payload=[VERSION,{k:design[k] for k in fields},stem_only]
    if image and design['color'] in ('#ffd524','#ffbb0b'):payload.append('bright-peel-2')
    elif image:payload.append('orange-peel-3')
    if design['cuts']:payload.append('manual-cuts-2')
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def cache_dir(kind):return DATA/'cache'/kind

def can_write(path):
    try:
        path.parent.mkdir(parents=True,exist_ok=True)
        return shutil.disk_usage(path.parent).free>40*1024*1024
    except OSError:return False

def build_cached(design,nu=96,nv=64):
    key=signature(design)+f'-{nu}x{nv}';path=cache_dir('meshes')/(key+'.json.gz')
    parts=_memory.get(key)
    if parts is None:
        try:
            raw=json.loads(gzip.decompress(path.read_bytes()));parts=[]
            for row in raw:
                part=Part(row['name'],row['vertices'],row['faces'],tuple(row['color']));part.normals=row['normals'];parts.append(part)
        except (OSError,ValueError,KeyError,TypeError,EOFError,zlib.error):
            parts=build(design,nu,nv)
            if can_write(path):
                try:path.write_bytes(gzip.compress(json.dumps([dict(name=p.name,vertices=p.vertices,faces=p.faces,color=p.color,normals=p.normals) for p in parts],separators=(',',':')).encode(),compresslevel=1))
                except OSError:pass
        _memory[key]=parts
    _memory.move_to_end(key)
    while len(_memory)>12:_memory.popitem(last=False)
    tint=tuple(int(design['color'][i:i+2],16)/255 for i in (1,3,5))
    result=[]
    for part in parts:
        p=copy.copy(part)
        if p.name in ('body','lid'):p.color=tint
        result.append(p)
    return result
