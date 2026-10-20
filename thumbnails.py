"""Cached Python 3D raster previews of the actual carved meshes.

Uses a depth buffer, so cavities, removable lids and candle parts occlude correctly.
No screenshot files or external artwork are needed.
"""
import copy,json
from collections import OrderedDict
from workers import WorkPool,render_preview
import numpy as np
from PySide6.QtGui import QImage
from mesh import body_info
from model_cache import build_cached,signature,cache_dir,can_write
from pathlib import Path
BUNDLED=Path(__file__).resolve().parent/'assets/previews'

_pool=WorkPool()
_cache=OrderedDict()

def shutdown_previews():_pool.shutdown(wait=False,cancel_futures=True)

def _generate(design,stem_only,path):
    image=render(design,stem_only=stem_only)
    if can_write(path):image.save(str(path),'PNG')
    return image

def preview(design,stem_only=False):
    key=signature(design,image=True,stem_only=stem_only)
    if key not in _cache:
        for path in (BUNDLED/(key+'.png'),cache_dir('previews')/(key+'.png')):
            image=QImage(str(path)) if path.exists() else QImage()
            if not image.isNull():
                _cache[key]=image;break
        else:
            path=cache_dir('previews')/(key+'.png')
            _cache[key]=_pool.submit(render_preview,copy.deepcopy(design),stem_only,path)
    _cache.move_to_end(key)
    while len(_cache)>128:
        old,item=next(iter(_cache.items()))
        if not isinstance(item,QImage) and not item.done():break
        _cache.pop(old)
    item=_cache[key]
    if isinstance(item,QImage):return item
    if not item.done():return None
    try:
        result=item.result();image=QImage.fromData(result,'PNG') if isinstance(result,bytes) else result
        if image.isNull():raise ValueError('Empty preview')
    except Exception:
        # Failed previews never escape a paint event or block the gallery buttons.
        image=QImage(300,270,QImage.Format_RGBA8888);image.fill(0)
    _cache[key]=image
    return image

def render(design,width=300,height=270,stem_only=False):
    parts=build_cached(design,48,32)
    parts=[p for p in parts if design['lit'] or p.name not in ('candle','wick','flame')]
    if stem_only:parts=[p for p in parts if p.name=='stem']
    # Front three-quarter elevation shows depth while keeping the face legible.
    yaw=.10;pitch=.12
    cy,sy=np.cos(yaw),np.sin(yaw);cp,sp=np.cos(pitch),np.sin(pitch)
    rotation=np.array([[cy,0,-sy],[-sp*sy,cp,-sp*cy],[cp*sy,sp,cp*cy]])
    transformed=[np.asarray(p.vertices)@rotation.T for p in parts]
    all_points=np.concatenate(transformed);lo=all_points.min(axis=0);hi=all_points.max(axis=0)
    scale=min((width-18)/(hi[0]-lo[0]),(height-18)/(hi[1]-lo[1]))
    centre=(lo+hi)/2
    pixels=np.zeros((height,width,4),dtype=np.uint8);depth=np.full((height,width),-np.inf)
    ink=np.array([93,30,0],dtype=np.uint8);amber=np.array([255,187,11],dtype=np.uint8)
    pale=np.array([255,252,120],dtype=np.uint8);red=np.array([255,82,0],dtype=np.uint8)
    orange=np.array([255,130,0],dtype=np.uint8)
    body=body_info(design);light=np.array([-.7,.8,1.]);light/=np.linalg.norm(light)
    for part,vertices in zip(parts,transformed):
        original=np.asarray(part.vertices);normals=np.asarray(part.normals)@rotation.T
        projected=np.column_stack(((vertices[:,0]-centre[0])*scale+width/2,
                                   height/2-(vertices[:,1]-centre[1])*scale,vertices[:,2]))
        peel=np.array([round(c*255) for c in part.color],dtype=np.uint8)
        for face in part.faces:
            ids=np.asarray(face);tri=projected[ids]
            x0,y0=tri[0,:2];x1,y1=tri[1,:2];x2,y2=tri[2,:2]
            det=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
            if det>=-1e-9:continue
            left=max(0,int(np.floor(tri[:,0].min())));right=min(width-1,int(np.ceil(tri[:,0].max())))
            top=max(0,int(np.floor(tri[:,1].min())));bottom=min(height-1,int(np.ceil(tri[:,1].max())))
            if left>right or top>bottom:continue
            yy,xx=np.mgrid[top:bottom+1,left:right+1];xx=xx+.5;yy=yy+.5
            a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/det
            b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/det;c=1-a-b
            z=a*tri[0,2]+b*tri[1,2]+c*tri[2,2]
            region=depth[top:bottom+1,left:right+1]
            mask=(a>=0)&(b>=0)&(c>=0)&(z>region)
            if not mask.any():continue
            normal=normals[ids].mean(axis=0);normal/=max(1e-9,np.linalg.norm(normal))
            point=original[ids].mean(axis=0)
            inside=np.dot(np.asarray(part.normals)[ids].mean(axis=0),point-[0,body['sy'],0])<0
            interpolated=a[...,None]*normals[ids[0]]+b[...,None]*normals[ids[1]]+c[...,None]*normals[ids[2]]
            lengths=np.maximum(1e-9,np.linalg.norm(interpolated,axis=2))
            shade=(interpolated@light)/lengths
            if part.name in ('stem','wick'):color=ink
            elif part.name=='candle':color=np.where((shade<.05)[...,None],amber,pale)
            elif part.name=='flame':color=pale if abs(point[0])<.02 else amber
            elif inside:color=(amber if point[1]<.8 else orange) if design['lit'] else ink
            elif peel[1]>158:color=np.where((shade<.12)[...,None],np.array([185,77,0],dtype=np.uint8),np.where((shade>.85)[...,None],pale,np.where((shade<.4)[...,None],orange,peel)))
            elif peel[1]<102:color=np.where((shade<.18)[...,None],np.array([185,77,0],dtype=np.uint8),np.where((shade>.94)[...,None],amber,np.where((shade>.76)[...,None],orange,peel)))
            else:color=np.where((shade<.12)[...,None],np.array([185,77,0],dtype=np.uint8),np.where((shade<.4)[...,None],red,np.where((shade>.96)[...,None],pale,np.where((shade>.8)[...,None],amber,peel))))
            region[mask]=z[mask];target=pixels[top:bottom+1,left:right+1];target[mask,:3]=color[mask] if color.ndim==3 else color;target[mask,3]=255
    # One-pixel ink silhouette, without drawing wireframes across the mesh.
    filled=pixels[:,:,3]>0;padded=np.pad(filled,1)
    surrounding=np.zeros_like(filled)
    for dx,dy in ((0,1),(1,0),(2,1),(1,2)):
        surrounding|=padded[dy:dy+height,dx:dx+width]
    outline=surrounding&~filled;pixels[outline,:3]=ink;pixels[outline,3]=255
    return QImage(pixels.data,width,height,width*4,QImage.Format_RGBA8888).copy()
