"""Stroke stabilization and exact bilateral reflection, independent of the UI."""
import math

def smooth_stroke(points,strength=.7):
    if len(points)<4 or strength<=0:return [list(p) for p in points]
    # Uniform arc-length sampling avoids dense jitter clusters around slow corners.
    clean=[list(points[0])]
    for p in points[1:]:
        if math.dist(p,clean[-1])>.003:clean.append(list(p))
    if len(clean)<4:return clean
    # Closed Chaikin interpolation rounds only within the convex hull of the stroke.
    rounds=1 if strength<.5 else 2
    weight=.08+.17*min(1,strength)
    for _ in range(rounds):
        result=[]
        for i,a in enumerate(clean):
            b=clean[(i+1)%len(clean)]
            result.extend([[a[k]*(1-weight)+b[k]*weight for k in (0,1)],[a[k]*weight+b[k]*(1-weight) for k in (0,1)]])
        clean=result
    if len(clean)>900:clean=[clean[round(i*len(clean)/900)] for i in range(900)]
    return clean

def mirrored_cuts(poly,mirror=False):
    cut=[list(p) for p in poly]
    if not mirror:return [cut]
    # Reverse winding as well as reflecting X. The geometry engine unions overlaps
    # when a stroke crosses the centreline, so no seam or double-thickness is created.
    return [cut,[[-x,y] for x,y in reversed(cut)]]


def is_mirror_pair(left,right):
    return len(left)==len(right) and all(abs(a[0]+b[0])<1e-9 and abs(a[1]-b[1])<1e-9 for a,b in zip(left,reversed(right)))


# Pick the real pumpkin hull, even when the cursor crosses an existing opening.
from functools import lru_cache
import numpy as np

@lru_cache(maxsize=8)
def _pick_mesh(key):
    from mesh import surface
    name,sx,sy,ribs,bulge=key;b=dict(id=name,sx=sx,sy=sy,ribs=ribs,bulge=bulge)
    nu=64;nv=48
    g=np.array([[surface(i*math.tau/nu,j*math.pi/nv,b) for i in range(nu)] for j in range(nv+1)])
    a=g[:-1];b=g[1:];c=np.roll(b,-1,axis=1);d=np.roll(a,-1,axis=1)
    t=np.concatenate([np.stack(v,axis=2).reshape(-1,3,3) for v in [(a,b,c),(a,c,d)]])
    t=t[t[:,:,2].mean(axis=1)>0]
    return t[:,0],t[:,1]-t[:,0],t[:,2]-t[:,0]

def face_hit(origin,direction,body):
    a,e1,e2=_pick_mesh(tuple(body[k] for k in ('id','sx','sy','ribs','bulge')))
    origin=np.asarray(origin);direction=np.asarray(direction)
    p=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,p)
    ok=np.abs(det)>1e-10;inv=np.zeros_like(det);inv[ok]=1/det[ok]
    tv=origin-a;u=np.einsum('ij,ij->i',tv,p)*inv;q=np.cross(tv,e1)
    v=q@direction*inv;t=np.einsum('ij,ij->i',e2,q)*inv
    ok&=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>=0)
    if not ok.any():return None
    hit=origin+direction*t[ok].min()
    if hit[2]<-1e-6:return None
    return [float(hit[0]/body['sx']),float((hit[1]-body['sy'])/body['sy'])]
