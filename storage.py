"""Local design validation and printable guide generation."""
import copy,json,math,os,re,sys
from pathlib import Path
from library import LIBRARY,default_design,PART_LIBRARY,face_polygons
from mesh import body_info
if sys.platform=="darwin":DATA=Path.home()/"Library/Application Support/PumpkinPatch"
elif sys.platform=="win32":DATA=Path(os.environ.get("APPDATA",Path.home()))/"PumpkinPatch"
else:DATA=Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))/"PumpkinPatch"
DATA=Path(os.environ.get("PUMPKIN_DATA",DATA))

def validate(raw):
    if not isinstance(raw,dict):raise ValueError('Expected a pumpkin design')
    d=copy.deepcopy(default_design())
    for key in d:
        if key in raw:d[key]=copy.deepcopy(raw[key])
    for key,lib in [('body','bodies'),('stem','stems'),('lid','lids')]:
        if d[key] is None and key!='body':continue
        if d[key] not in [x['id'] for x in LIBRARY[lib]]:raise ValueError('Unknown '+key)
    if not isinstance(d['name'],str):raise ValueError('Invalid name')
    d['name']=d['name'][:80]
    if not isinstance(d['color'],str) or d['color'] not in ['#ff8200','#ff5200','#ffbb0b','#ff9200','#ffd524']:raise ValueError('Choose a palette color')
    def number(value,lo,hi):
        if not isinstance(value,(float,int)) or not math.isfinite(value) or not lo<=value<=hi:raise ValueError('Invalid feature dimensions')
    number(d['size'],15,50)
    if set(d['parts'])!=set(default_design()['parts']):raise ValueError('Missing feature slots')
    for key,part in d['parts'].items():
        lib=PART_LIBRARY.get(key,'teeth')
        if part.get('feature') is not None and part['feature'] not in [x['id'] for x in LIBRARY[lib]]:raise ValueError('Unknown '+key+' feature')
        for axis in ['x','y']:number(part[axis],-1.5,1.5)
        for axis in ['sx','sy']:number(part[axis],.02,2)
        number(part['rotation'],-180,180)
        if not isinstance(part['visible'],bool):raise ValueError('Invalid visibility')
    if not isinstance(d['cuts'],list) or len(d['cuts'])>80:raise ValueError('Too many custom cuts')
    for poly in d['cuts']:
        if not 3<=len(poly)<=1000:raise ValueError('Invalid carving stroke')
        for point in poly:
            if len(point)!=2:raise ValueError('Invalid carving point')
            for n in point:number(n,-1.3,1.3)
    if d['id'] is not None and not re.fullmatch('[a-f0-9]{32}',d['id']):raise ValueError('Invalid pumpkin ID')
    d['lit']=bool(d['lit']);d['version']=2
    return d

def write_guide(d):
    import html
    cuts,teeth=face_polygons(d);b=body_info(d);width=d['size']*10;height=width*b['sy']/b['sx'];scale=min(1,175/width,205/height)
    def svgpolys(polys,color):return ''.join('<polygon fill="'+color+'" points="'+' '.join(f'{100+x*100:.3f},{100-y*100:.3f}' for x,y in p)+'"/>' for p in polys)
    title=html.escape(d['name'] or 'My pumpkin')
    return f'''<!doctype html><html><meta charset="utf-8"><title>{title} — carving guide</title><style>@page{{size:A4;margin:15mm}}body{{font:15px/1.5 system-ui;max-width:180mm;margin:20px auto;color:#5d1e00}}h1{{font-size:32px}}li{{margin:14px 0}}.pattern{{break-before:page;text-align:center}}svg{{display:block;margin:10mm auto}}@media print{{button{{display:none}}}}</style><h1>{title}</h1><p>Pumpkin Patch · {d['size']:g} cm target width · {html.escape(b['name'])}</p><button onclick="print()">Print guide</button><h2>Gather your tools</h2><p>Washable marker, tape, pin, scoop, pumpkin saw, and a battery LED candle.</p><ol><li>Wash and dry your pumpkin. Choose a flat side for the face.</li><li>An adult should cut an angled lid with a small alignment notch. Scoop out the pulp and thin the face evenly to about 2–3 cm.</li><li>Tape the template to the pumpkin. Snip the paper edges to fit the curve. Prick along the dark boundaries, remove the paper and connect the dots.</li><li>Cut the dark regions, starting with the smallest shapes. Leave white teeth and bridges intact. Use short saw strokes and keep your free hand away from the blade.</li><li>Put a battery LED inside, replace the lid, and enjoy your pumpkin.</li></ol><p>Children need adult help with cutting. Digital geometry is stylized: widen fragile bridges and adjust the design to your real pumpkin. Use an LED to avoid heat and flame.</p><section class="pattern"><h2>Carving pattern</h2><p>Cut dark areas. Keep white teeth and bridges.</p><svg xmlns="http://www.w3.org/2000/svg" width="{width*scale:.1f}mm" height="{height*scale:.1f}mm" viewBox="0 0 200 200" preserveAspectRatio="none"><ellipse cx="100" cy="100" rx="98" ry="98" fill="none" stroke="#aaa" stroke-dasharray="2 2" stroke-width=".5"/>{svgpolys(cuts,'#222')}{svgpolys(teeth,'white')}{svgpolys(d['cuts'],'#222')}</svg><p>Print at 100%. Pattern is {scale*100:.1f}% of target size, {width*scale/10:.1f} × {height*scale/10:.1f} cm.<br>{'Enlarge by '+str(round(100/scale))+'% for the target size.' if scale<1 else ''} Flat projection; adjust to the pumpkin curvature.</p><svg xmlns="http://www.w3.org/2000/svg" width="50mm" height="10mm" viewBox="0 0 50 10"><path d="M0 0V5H50V0" stroke="black" fill="none"/><text x="25" y="9" font-size="3" text-anchor="middle">5 cm calibration</text></svg></section></html>'''

