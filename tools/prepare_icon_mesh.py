"""Recreate the original icon's tiny eyes and open two-tooth grin in real 3D."""
import sys,json,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mesh import build
from library import default_design
out=ROOT/'assets/icons'
d=default_design();d['name']='Pumpkin Patch icon';d['stem']='crook'
from library import oval
# Trace the original vector icon, including both teeth, into a single cut outline.
points=[(309,517)];current=points[0]
def line(point):
    global current
    points.append(point);current=point
def curve(*controls):
    global current
    start=current;n=16
    for i in range(1,n+1):
        t=i/n;u=1-t
        if len(controls)==2:
            a,b=controls;point=tuple(u*u*start[k]+2*u*t*a[k]+t*t*b[k] for k in (0,1))
        else:
            a,b,c=controls;point=tuple(u**3*start[k]+3*u*u*t*a[k]+3*u*t*t*b[k]+t**3*c[k] for k in (0,1))
        points.append(point)
    current=controls[-1]
curve((361,500),(425,507));line((426,571));curve((445,584),(463,571));line((463,507))
line((485,508));line((485,572));curve((503,585),(523,571));line((524,507))
curve((642,499),(720,516));curve((731,581),(713,697),(662,749))
curve((608,810),(432,819),(369,762));curve((317,716),(291,598),(309,517))
d['cuts']=[oval(.050,.085,n=40,cx=-.335,cy=.53),oval(.049,.081,n=40,cx=.355,cy=.53),
           [[(x-512)/350,(591-y)/350] for x,y in points[:-1]]]
parts=build(d,160,100)
rows=[dict(name=p.name,vertices=p.vertices,faces=p.faces,normals=p.normals) for p in parts if p.name in ('body','lid','stem')]
(out/'icon-mesh.json.gz').write_bytes(gzip.compress(json.dumps(rows,separators=(',',':')).encode()))
(out/'icon-design.pumpkin').write_text(json.dumps(d,indent=2))
print('Prepared closed 3D icon meshes:',[(p['name'],len(p['faces'])) for p in rows])
