"""Dependency-free hollow pumpkin meshes and glTF 2.0 binary export. Units: metres."""
import json, math, struct
from dataclasses import dataclass, field, asdict
from pathlib import Path

SHAPES = {'Classic': (1, 1), 'Tall': (.86, 1.24), 'Squat': (1.15, .78)}
EYES = {'Triangles': [(-.14,-.10),(.14,-.10),(0,.16)],
        'Diamonds': [(0,-.16),(.14,0),(0,.16),(-.14,0)],
        'Sleepy': [(-.17,0),(.16,-.04),(.13,.07),(-.13,.09)],
        'Round': [(math.cos(i*math.tau/16)*.14,math.sin(i*math.tau/16)*.14) for i in range(16)]}
MOUTHS = {'Grin': [(-.53,-.05),(-.32,-.15),(0,-.19),(.32,-.15),(.53,-.05),(.39,-.32),(.14,-.39),(-.14,-.39),(-.39,-.32)],
          'Fangs': [(-.53,-.06),(-.24,-.09),(-.20,-.23),(-.10,-.09),(.10,-.09),(.20,-.23),(.24,-.09),(.53,-.06),(.37,-.34),(-.37,-.34)],
          'Surprised': [(math.cos(i*math.tau/20)*.23,math.sin(i*math.tau/20)*.27-.18) for i in range(20)],
          'Zigzag': [(-.54,-.10),(-.34,-.02),(-.14,-.12),(.07,-.02),(.28,-.12),(.51,-.02),(.43,-.23),(.24,-.30),(.04,-.20),(-.16,-.30),(-.36,-.20),(-.50,-.28)]}

@dataclass
class Design:
    name: str = 'Little mischief'
    shape: str = 'Classic'
    eyes: str = 'Triangles'
    nose: str = 'Triangle'
    mouth: str = 'Grin'
    size: float = 30
    eye_spacing: float = .34
    feature_scale: float = 1
    color: str = '#e88930'
    cuts: list = field(default_factory=list)
    completed: bool = False
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls, data):
        d = cls(**{k:v for k,v in data.items() if k in cls.__dataclass_fields__})
        if d.shape not in SHAPES or d.eyes not in EYES or d.mouth not in MOUTHS or d.nose not in ('Triangle','Diamond','None'):
            raise ValueError('Unknown pumpkin feature')
        if not 15 <= float(d.size) <= 50 or not .6 <= float(d.feature_scale) <= 1.4 or not .22 <= float(d.eye_spacing) <= .48:
            raise ValueError('Design dimensions out of range')
        if len(d.cuts)>100 or any(len(p)>2000 for p in d.cuts): raise ValueError('Too many carving points')
        if any(not math.isfinite(float(c)) or abs(float(c))>2 for p in d.cuts for point in p for c in point): raise ValueError('Invalid carving point')
        if len(d.color)!=7 or d.color[0]!='#': raise ValueError('Invalid color')
        int(d.color[1:],16)
        return d

def polygons(d):
    result=[]
    for side in (-1,1):
        result.append([(x*d.feature_scale+side*d.eye_spacing,y*d.feature_scale+.26) for x,y in EYES[d.eyes]])
    if d.nose!='None':
        p=[(-.09,-.06),(.09,-.06),(0,.10)] if d.nose=='Triangle' else [(0,-.10),(.09,0),(0,.10),(-.09,0)]
        result.append(p)
    result.append([(x*d.feature_scale,y*d.feature_scale-.14) for x,y in MOUTHS[d.mouth]])
    return result+d.cuts

def inside(x,y,poly):
    hit=False
    for i,(ax,ay) in enumerate(poly):
        bx,by=poly[i-1]
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax: hit=not hit
    return hit

def point(theta,phi,d,inner=False):
    sx,sy=SHAPES[d.shape]
    r=math.sin(phi)*(1+.075*math.cos(10*theta))
    # Keep the inner shell safely inside even at the ribs.
    factor=.88 if inner else 1
    return (sx*r*math.sin(theta)*factor,sy*(math.cos(phi)*factor+1),sx*r*math.cos(theta)*factor)

@dataclass
class Part:
    name: str
    vertices: list
    faces: list
    color: tuple


def shell(d,nu=80,nv=48):
    """Closed tiled shell: openings remove cells; boundary quads expose flesh.
    Lid and body share a seam, but each is independently closed for printing.
    """
    masks=polygons(d)
    split=round(nv*.25)
    parts=[]
    for name,lo,hi in [('lid',0,split),('body',split,nv)]:
        cells=set()
        for j in range(lo,hi):
            phi=math.pi*(j+.5)/nv
            for i in range(nu):
                theta=math.tau*(i+.5)/nu
                x,y,z=point(theta,phi,d)
                sx,sy=SHAPES[d.shape]
                cut=z>0 and any(inside(x/sx,(y-sy)/sy,p) for p in masks)
                if name=='lid' or not cut: cells.add((i,j))
        verts=[]; faces=[]; lookup={}
        def vertex(i,j,inner):
            p=point(math.tau*(i%nu)/nu,math.pi*j/nv,d,inner)
            key=tuple(round(v,10) for v in p)
            if key not in lookup: lookup[key]=len(verts); verts.append(p)
            return lookup[key]
        def quad(items):
            ids=[vertex(*v) for v in items]
            ids=list(dict.fromkeys(ids))
            if len(ids)==3: faces.append(tuple(ids))
            elif len(ids)==4: faces.extend([(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])])
        for i,j in sorted(cells):
            corners=[(i,j),(i,j+1),(i+1,j+1),(i+1,j)]
            quad([(a,b,False) for a,b in corners])
            quad([(a,b,True) for a,b in reversed(corners)])
            neighbors=[((i-1)%nu,j),(i,j+1),((i+1)%nu,j),(i,j-1)]
            for k,neighbor in enumerate(neighbors):
                if neighbor not in cells:
                    a,b=corners[k],corners[(k+1)%4]
                    quad([(*b,False),(*a,False),(*a,True),(*b,True)])
        color=tuple(int(d.color[i:i+2],16)/255 for i in (1,3,5))
        parts.append(Part(name,verts,faces,color))
    return parts

def cylinder(name,radius,height,y,color,n=16,x=0,z=0):
    v=[(x+radius*math.cos(i*math.tau/n),y+h,z+radius*math.sin(i*math.tau/n)) for h in (0,height) for i in range(n)]
    v.extend([(x,y,z),(x,y+height,z)])
    f=[]
    for i in range(n):
        k=(i+1)%n
        f.extend([(i,n+i,n+k),(i,n+k,k),(2*n,i,k),(2*n+1,n+k,n+i)])
    return Part(name,v,f,color)

def model(d,nu=80,nv=48,candle=True):
    p=shell(d,nu,nv); sy=SHAPES[d.shape][1]
    p.append(cylinder('stem',.105,.32,sy*2-.025,(.23,.30,.12),12))
    if candle: p.append(cylinder('candle',.14,.44,.15,(1,.88,.55)))
    return p

def export_glb(d,path,parts=None):
    """Indexed glTF meshes with portable palette materials and baked doodle shading.

    KHR_materials_unlit preserves palette colors without adding studio lighting:
    https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_materials_unlit
    """
    import numpy as np
    parts=model(d) if parts is None else parts
    binary=bytearray();views=[];acc=[];meshes=[];materials=[];nodes=[];unlit=False
    def linear(values):
        values=np.asarray(values,dtype=np.float64)
        return np.where(values<=.04045,values/12.92,((values+.055)/1.055)**2.4)
    def accessor(values,kind,component=5126,target=34962,bounds=False):
        dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[component];values=np.asarray(values,dtype=dtype)
        while len(binary)%4:binary.append(0)
        raw=values.tobytes();view=len(views);views.append(dict(buffer=0,byteOffset=len(binary),byteLength=len(raw),target=target));binary.extend(raw)
        entry=dict(bufferView=view,componentType=component,count=len(values),type=kind)
        if bounds:entry.update(min=values.min(axis=0).tolist(),max=values.max(axis=0).tolist())
        acc.append(entry);return len(acc)-1
    scale=getattr(d,'scale',d.size/200)
    for part in parts:
        vertices=np.asarray(part.vertices,dtype=np.float64);faces=np.asarray(part.faces,dtype=np.int64)
        if not len(vertices) or not len(faces):continue
        colors=np.asarray(part.colors) if hasattr(part,'colors') else None
        if hasattr(part,'normals'):normals=np.asarray(part.normals,dtype=np.float64)
        else:
            triangles=vertices[faces];n=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);length=np.linalg.norm(n,axis=1);valid=length>1e-10
            if colors is not None:colors=colors[faces[valid]].reshape(-1,3)
            vertices=triangles[valid].reshape(-1,3);normals=np.repeat(n[valid]/length[valid,None],3,axis=0);faces=np.arange(len(vertices)).reshape(-1,3)
        if not len(vertices):continue
        normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-10)
        attributes={'POSITION':accessor(vertices*scale,'VEC3',bounds=True),'NORMAL':accessor(normals,'VEC3')}
        primitives=[]
        if colors is not None:
            # Material colors also work in importers that discard COLOR_0.
            # Keep original normals/vertices shared across palette boundaries.
            palette=np.unique(colors,axis=0)
            means=colors[faces].mean(axis=1)
            labels=np.argmin(((means[:,None,:]-palette[None,:,:])**2).sum(axis=2),axis=1)
            groups=[(color,faces[labels==i]) for i,color in enumerate(palette) if np.any(labels==i)]
        else:groups=[(part.color,faces)]
        for color,group in groups:
            material=dict(name=part.name+' palette '+str(len(materials)),pbrMetallicRoughness=dict(baseColorFactor=[*linear(color).tolist(),1],metallicFactor=0,roughnessFactor=1))
            if colors is not None:
                material['extensions']={'KHR_materials_unlit':{}};unlit=True
            materials.append(material)
            indices=accessor(group.reshape(-1),'SCALAR',5123 if len(vertices)<=65536 else 5125,34963)
            primitives.append(dict(attributes=attributes,indices=indices,material=len(materials)-1,mode=4))
        meshes.append(dict(name=part.name,primitives=primitives))
        nodes.append(dict(mesh=len(meshes)-1,name=part.name))
    doc=dict(asset=dict(version='2.0',generator='Pumpkin Patch'),scene=0,scenes=[dict(nodes=list(range(len(nodes))))],nodes=nodes,meshes=meshes,materials=materials,buffers=[dict(byteLength=len(binary))],bufferViews=views,accessors=acc,extras=dict(design=d.to_dict(),units='metres',note='Separate closed meshes; smooth crease normals; static front-view doodle colors.'))
    if unlit:doc['extensionsUsed']=['KHR_materials_unlit']
    js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
    payload=struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    Path(path).write_bytes(struct.pack('<III',0x46546c67,2,len(payload)+12)+payload)
