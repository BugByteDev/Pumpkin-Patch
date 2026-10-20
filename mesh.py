"""Actual hollow mesh carving and binary glTF export; no runtime Blender dependency."""
import json,math,gzip
from pathlib import Path
from library import LIBRARY,face_polygons
from legacy_mesh import Part,cylinder,inside,export_glb as glb

ASSETS=Path(__file__).resolve().parent/'assets'
_cache={}
def body_info(d):return next(b for b in LIBRARY['bodies'] if b['id']==d['body'])
def surface(theta,phi,body,inner=False):
    f=.875 if inner else 1
    sin_phi=math.sin(phi);cos_phi=math.cos(phi)
    # Full shoulders and gentle ribs that converge into the stem socket.
    round_body=body['id']=='round'
    rib_depth=.045 if round_body else .065
    shoulder_power=.94 if round_body else .82
    rib=1+(rib_depth*math.cos(body['ribs']*theta)+.004*math.cos(body['ribs']*theta*2))*sin_phi**.55
    r=max(0,sin_phi)**shoulder_power*rib*(1+body['bulge']*cos_phi)
    # Slightly fuller shoulders above the waist, with a narrower resting base.
    r*=1+.025*cos_phi*sin_phi
    if body['id']=='lumpy':r*=1+.025*math.sin(theta*3+phi*2)
    # A recessed stem socket and tucked-in base replace spherical poles.
    cap_dip=.14*math.copysign(1,cos_phi)*math.exp(-(sin_phi/.34)**2)
    y=cos_phi-cap_dip
    return (body['sx']*r*math.sin(theta)*f,body['sy']*(y*f+1),body['sx']*r*math.cos(theta)*f)

def stem_part(kind,body):
    """A flared, ridged stalk swept along each style's own curved centreline."""
    import numpy as np
    segments=32;steps=24;base=surface(0,0,body)[1]-.035
    height={'stub':.19,'tall':.56,'crook':.40,'curl':.53,'lean':.39,'wide':.29}[kind]
    radius=.15 if kind=='wide' else .092
    def centre(t):
        x=z=0.;y=height*t
        if kind=='crook':x=.23*t*t;z=.025*math.sin(t*math.pi)
        if kind=='lean':x=.27*t;z=-.06*t
        if kind=='tall':x=.035*math.sin(t*2);z=.025*t*t
        if kind=='curl':
            a=t*2.45;x=.20*(1-math.cos(a));y=.27*math.sin(a)+.14*t;z=.045*t*t
        return np.array([x,base+y,z])
    vertices=[];faces=[]
    for j in range(steps+1):
        t=j/steps;c=centre(t)
        tangent=centre(min(1,t+.001))-centre(max(0,t-.001));tangent/=np.linalg.norm(tangent)
        u=np.cross(tangent,[0,0,1]);u/=np.linalg.norm(u);v=np.cross(u,tangent)
        # Broad attachment, woody taper, and six shallow lengthwise furrows.
        r=radius*(1-.40*t)+.065*math.exp(-t*14)
        for i in range(segments):
            a=math.tau*i/segments
            rr=r*(1+.09*math.cos(a*6+.3*t)+.025*math.sin(a*3))
            point=c+rr*(math.cos(a)*u+math.sin(a)*v)
            vertices.append(tuple(point))
    for j in range(steps):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments
            faces.extend([(a,a+segments,b+segments),(a,b+segments,b)])
    bottom=len(vertices);vertices.append(tuple(centre(0)))
    top=len(vertices);vertices.append(tuple(centre(1)))
    for i in range(segments):
        k=(i+1)%segments
        faces.extend([(bottom,i,k),(top,steps*segments+k,steps*segments+i)])
    return Part('stem',vertices,faces,(.365,.118,0))

def candle_parts(body):
    """Closed wax, wick and flame meshes resting on the inner shell floor."""
    base=surface(0,math.pi,body,inner=True)[1]+.018
    def rings(name,profiles,segments,bottom,top,color,wax=False):
        vertices=[];faces=[]
        for row,(radius,h,lean) in enumerate(profiles):
            for i in range(segments):
                a=math.tau*i/segments;r=radius;y=h
                if wax and 2<=row<=7:
                    for angle,low in [(.4,.22),(2.15,.29),(3.75,.34),(5.3,.25)]:
                        delta=math.atan2(math.sin(a-angle),math.cos(a-angle))
                        drip=math.exp(-(delta/.15)**2)*(.5+.5*math.tanh((h-low)/.018))
                        r+=.015*drip*math.exp(-((h-.40)/.18)**4)
                if wax and row in (6,7,8,9):
                    y+=(.009*math.sin(a*3)+.005*math.cos(a*5))*(1 if row in (7,8) else .5)
                vertices.append((lean+r*math.cos(a),base+y,r*math.sin(a)))
        for j in range(len(profiles)-1):
            for i in range(segments):
                a=j*segments+i;b=j*segments+(i+1)%segments
                faces.extend([(a,a+segments,b+segments),(a,b+segments,b)])
        bottom_index=len(vertices);vertices.append((bottom[0],base+bottom[1],0))
        top_index=len(vertices);vertices.append((top[0],base+top[1],0))
        last=(len(profiles)-1)*segments
        for i in range(segments):
            k=(i+1)%segments
            faces.extend([(bottom_index,i,k),(top_index,last+k,last+i)])
        return Part(name,vertices,faces,color)
    profile=[(.125,0),(.143,.018),(.145,.16),(.145,.23),(.145,.30),(.146,.37),
             (.149,.435),(.15,.475),(.128,.477),(.107,.448),(.064,.422),(.018,.42)]
    wax=rings('candle',[(r,h,0) for r,h in profile],48,(0,0),(0,.42),(1,.988,.471),True)
    wick=cylinder('wick',.008,.087,base+.418,(.365,.118,0),12)
    flame=rings('flame',[(.008,.503,0),(.033,.521,0),(.050,.555,.001),(.048,.595,.004),
                         (.033,.643,.010),(.018,.693,.020),(.005,.741,.031)],28,
                (0,.498),(.034,.76),(1,.733,.043))
    return [wax,wick,flame]

def get_grid(d,nu,nv):
    key=(d['body'],nu,nv)
    if key not in _cache:
        b=body_info(d)
        _cache[key]=[[surface(math.tau*i/nu,math.pi*j/nv,b,inner) for j in range(nv+1) for i in range(nu)] for inner in (False,True)]
    return _cache[key]

def build(d,nu=96,nv=64):
    b=body_info(d);grid=get_grid(d,nu,nv);cuts,teeth=face_polygons(d)
    def prepared(poly):return (min(x for x,y in poly),min(y for x,y in poly),max(x for x,y in poly),max(y for x,y in poly),poly)
    masks=[prepared(p) for p in cuts];blocks=[prepared(p) for p in teeth]
    def hit(x,y,polys):return any(l<=x<=r and bot<=y<=top and inside(x,y,p) for l,bot,r,top,p in polys)
    removed=set()
    for j in range(1,nv-1):
        phi=math.pi*(j+.5)/nv
        for i in range(nu):
            theta=math.tau*(i+.5)/nu
            x,y,z=surface(theta,phi,b)
            if z<=0:continue
            x/=b['sx'];y=(y-b['sy'])/b['sy']
            if hit(x,y,masks) and not hit(x,y,blocks):removed.add((i,j))
    # Eliminate diagonal-only contacts, which would create nonmanifold cut walls.
    for _ in range(8):
        additions=set()
        for i,j in removed:
            right=((i+1)%nu,j);down=(i,j+1);diag=((i+1)%nu,j+1)
            if diag in removed and right not in removed and down not in removed:additions.add(right)
            if right in removed and down in removed and diag not in removed:additions.add(diag)
        if not additions:break
        removed.update(p for p in additions if 0<p[1]<nv-1)
    split=round(nv*{'low':.20,'high':.30}.get(d['lid'],.25))
    def seam(i):return split+(1 if d['lid']=='zigzag' and (i//4)%2 else 0)
    color=tuple(int(d['color'][i:i+2],16)/255 for i in (1,3,5));parts=[]
    for name in ['body','lid']:
        if name=='lid' and d['lid'] is None:continue
        cells={(i,j) for j in range(nv) for i in range(nu) if (j>=seam(i) if name=='body' else j<seam(i)) and (i,j) not in removed}
        vertices=[];faces=[];lookup={}
        def v(i,j,inner):
            p=grid[int(inner)][j*nu+i%nu];key=tuple(round(x,8) for x in p)
            if key not in lookup:lookup[key]=len(vertices);vertices.append(p)
            return lookup[key]
        def quad(items):
            ids=list(dict.fromkeys(v(*p) for p in items))
            if len(ids)==3:faces.append(tuple(ids))
            if len(ids)==4:faces.extend([(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])])
        for i,j in sorted(cells):
            corners=[(i,j),(i,j+1),(i+1,j+1),(i+1,j)]
            quad([(*p,False) for p in corners]);quad([(*p,True) for p in reversed(corners)])
            neighbors=[((i-1)%nu,j),(i,j+1),((i+1)%nu,j),(i,j-1)]
            for k,neighbor in enumerate(neighbors):
                if neighbor not in cells:
                    a,c=corners[k],corners[(k+1)%4];quad([(*c,False),(*a,False),(*a,True),(*c,True)])
        parts.append(Part(name,vertices,faces,color))
    if d['stem'] and d['lid']:parts.append(stem_part(d['stem'],b))
    parts.extend(candle_parts(b))
    return parts

def packed(d,nu=96,nv=64):
    return [dict(name=p.name,vertices=p.vertices,faces=p.faces,color=p.color) for p in build(d,nu,nv)]

def export(d,path):
    from export_style import split_color_boundaries
    outer=get_grid(d,160,100)[0];width=max(p[0] for p in outer)-min(p[0] for p in outer)
    class Adapter:
        size=d['size'];scale=d['size']/100/width
        def to_dict(self):return d
    parts=[p for p in build(d,160,100) if d['lit'] or p.name not in ('candle','wick','flame')]
    for part in parts:split_color_boundaries(part,d)
    glb(Adapter(),path,parts)

# Smooth Boolean carving replaces the earlier raster-cell prototype.
_grid_build=build
_bare_cache={}
def build(d,nu=96,nv=64):
    import copy
    import numpy as np
    from manifold3d import Manifold,Mesh,CrossSection,FillRule
    b=body_info(d)
    def sections(polys):
        return CrossSection.compose([CrossSection([np.array(p,dtype=np.float64)],FillRule.EvenOdd) for p in polys if len(p)>=3])
    cuts,teeth=face_polygons(dict(d,cuts=[]))
    # Freehand cuts remove preset teeth too, instead of treating them as protected.
    cut=(sections(cuts)-sections(teeth))+sections(d['cuts'])
    cutter=cut.extrude(2.5).scale((b['sx'],b['sy'],b['sx'])).translate((0,b['sy'],0))
    key=(d['body'],d['lid'],d['stem'],nu,nv)
    if key not in _bare_cache:
        bare=copy.deepcopy(d);bare['cuts']=[]
        for p in bare['parts'].values():p['feature']=None
        bases=_grid_build(bare,nu,nv)
        cached=[]
        for p in bases:
            solid=Manifold(Mesh(np.array(p.vertices,dtype=np.float32),np.array(p.faces,dtype=np.uint32)))
            if str(solid.status())!='Error.NoError':raise ValueError('Invalid base mesh: '+str(solid.status()))
            cached.append((p,solid))
        _bare_cache[key]=cached
        while len(_bare_cache)>6:_bare_cache.pop(next(iter(_bare_cache)))
    result=[]
    for part,solid in _bare_cache[key]:
        shape=solid-cutter if part.name in ('body','lid') and not cut.is_empty() else solid
        if str(shape.status())!='Error.NoError':raise ValueError('Carving could not produce a valid mesh')
        if shape.is_empty():continue
        mesh=shape.calculate_normals(0,48).to_mesh()
        props=np.asarray(mesh.vert_properties)
        color=tuple(int(d['color'][i:i+2],16)/255 for i in (1,3,5)) if part.name in ('body','lid') else part.color
        p=Part(part.name,props[:,:3].tolist(),np.asarray(mesh.tri_verts).tolist(),color)
        p.normals=props[:,3:6].tolist()
        result.append(p)
    return result

def packed(d,nu=96,nv=64):
    return [dict(name=p.name,vertices=p.vertices,faces=p.faces,normals=p.normals,color=p.color) for p in build(d,nu,nv)]
