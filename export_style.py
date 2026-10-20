"""Bake front-view doodle lighting into portable palette materials.

Colors here are sRGB; the writer converts material factors to linear values.
The bake is static: the app's moving candlelight remains an interactive effect.
"""
import math
import numpy as np
from mesh import body_info,surface

def bake_colors(part,design):
    positions=np.asarray(part.vertices);normals=np.asarray(part.normals)
    normals=normals/np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-10)
    light=np.array([-.7,.8,1.]);light/=np.linalg.norm(light);shade=normals@light
    ink=np.array([93,30,0])/255;amber=np.array([255,187,11])/255
    pale=np.array([255,252,120])/255;red=np.array([255,82,0])/255
    orange=np.array([255,130,0])/255;burnt=np.array([185,77,0])/255
    if part.name in ('stem','wick'):colors=np.tile(ink,(len(positions),1))
    elif part.name=='candle':
        lamp=np.array([-.6,.5,1.]);lamp/=np.linalg.norm(lamp)
        colors=np.where(((normals@lamp)<.05)[:,None],amber,pale)
    elif part.name=='flame':
        base=surface(0,math.pi,body_info(design),inner=True)[1]+.018+.498
        h=positions[:,1]-base;core=.022*np.sqrt(np.maximum(0,1-((h-.085)/.095)**2))
        colors=np.where(((np.abs(positions[:,0])<core)&(h<.18))[:,None],pale,amber)
    else:
        peel=np.asarray(part.color)
        if peel[1]>.62:
            colors=np.where((shade<.12)[:,None],burnt,np.where((shade>.85)[:,None],pale,np.where((shade<.4)[:,None],orange,peel)))
        elif peel[1]<.4:
            colors=np.where((shade<.18)[:,None],burnt,np.where((shade>.94)[:,None],amber,np.where((shade>.76)[:,None],orange,peel)))
        else:
            colors=np.where((shade<.12)[:,None],burnt,np.where((shade<.4)[:,None],red,np.where((shade>.96)[:,None],pale,np.where((shade>.8)[:,None],amber,peel))))
        inside=np.einsum('ij,ij->i',normals,positions-[0,body_info(design)['sy'],0])<0
        cavity=np.where((positions[:,1]<.8)[:,None],amber,orange) if design['lit'] else ink
        colors=np.where(inside[:,None],cavity,colors)
    return colors.tolist()


def split_color_boundaries(part, design):
    """Clip crossing triangles at shader thresholds instead of snapping whole faces.

    New positions and normals are interpolated on the existing surface. Each
    resulting polygon gets one ordinary material, with no vertex-color support
    needed in the viewer.
    """
    from types import SimpleNamespace
    p=np.asarray(part.vertices,dtype=float);n=np.asarray(part.normals,dtype=float)
    n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-10)
    colors=np.asarray(bake_colors(part,design));faces=np.asarray(part.faces)
    if part.name in ('stem','wick'):
        part.colors=colors.tolist();return part
    if part.name=='candle':
        lamp=np.array([-.6,.5,1.]);lamp/=np.linalg.norm(lamp)
        fields=(n@lamp-.05)[:,None]
    elif part.name=='flame':
        base=surface(0,math.pi,body_info(design),inner=True)[1]+.018+.498
        h=p[:,1]-base;core=.022*np.sqrt(np.maximum(0,1-((h-.085)/.095)**2))
        fields=np.column_stack((core-np.abs(p[:,0]),h-.18))
    else:
        light=np.array([-.7,.8,1.]);light/=np.linalg.norm(light)
        shade=n@light
        levels=(.12,.4,.85) if part.color[1]>.62 else ((.18,.76,.94) if part.color[1]<.4 else (.12,.4,.8,.96))
        inner=np.einsum('ij,ij->i',n,p-[0,body_info(design)['sy'],0])
        fields=np.column_stack([shade-level for level in levels]+[inner,p[:,1]-.8])
    uniform=np.all(colors[faces]==colors[faces[:,0,None]],axis=(1,2))
    result=faces[uniform].tolist();vertices=p.tolist();normals=n.tolist();out_colors=colors.tolist()
    samples=[];polygons=[]
    def clip(poly,values,positive):
        out=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            da=float(a@values);db=float(b@values)
            ina=da>=-1e-12 if positive else da<=1e-12
            inb=db>=-1e-12 if positive else db<=1e-12
            if ina:out.append(a)
            if ina!=inb and abs(da-db)>1e-14:out.append(a+(b-a)*(da/(da-db)))
        return out
    for ids in faces[~uniform]:
        polys=[[row for row in np.eye(3)]]
        for values in fields[ids].T:
            new=[]
            for poly in polys:
                v=np.array(poly)@values
                if v.min() < -1e-10 and v.max() > 1e-10:
                    new.extend(q for q in (clip(poly,values,True),clip(poly,values,False)) if len(q)>=3)
                else:new.append(poly)
            polys=new
        for poly in polys:
            weights=np.asarray(poly);xyz=weights@p[ids];norm=weights@n[ids]
            if sum(np.linalg.norm(np.cross(xyz[i]-xyz[0],xyz[i+1]-xyz[0])) for i in range(1,len(xyz)-1))<1e-14:continue
            samples.append((xyz.mean(axis=0),norm.mean(axis=0)))
            polygons.append((xyz,norm))
    if samples:
        proxy=SimpleNamespace(name=part.name,color=part.color,vertices=[s[0] for s in samples],normals=[s[1] for s in samples])
        shades=bake_colors(proxy,design)
        for (xyz,norm),color in zip(polygons,shades):
            start=len(vertices);vertices.extend(xyz.tolist());normals.extend(norm.tolist());out_colors.extend([color]*len(xyz))
            result.extend((start,start+i,start+i+1) for i in range(1,len(xyz)-1))
    part.vertices=vertices;part.normals=normals;part.faces=result;part.colors=out_colors
    return part
