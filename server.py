"""Local-only application server. Data stays in the user's application directory."""
import copy,json,math,os,re,secrets,sys,tempfile,threading,uuid
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from library import LIBRARY,default_design,PART_LIBRARY,face_polygons
from mesh import packed,export,body_info
ROOT=Path(__file__).resolve().parent
if sys.platform=='darwin':DATA=Path.home()/'Library/Application Support/PumpkinPatch'
elif sys.platform=='win32':DATA=Path(os.environ.get('APPDATA',Path.home()))/'PumpkinPatch'
else:DATA=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'PumpkinPatch'
DATA=Path(os.environ.get('PUMPKIN_DATA',DATA))
TOKEN=secrets.token_urlsafe(24)

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
    return f'''<!doctype html><html><meta charset="utf-8"><title>{title} — carving guide</title><style>@page{{size:A4;margin:15mm}}body{{font:15px/1.5 system-ui;max-width:180mm;margin:20px auto;color:#5d1e00}}h1{{font-size:32px}}li{{margin:14px 0}}.pattern{{break-before:page;text-align:center}}svg{{display:block;margin:10mm auto}}@media print{{button{{display:none}}}}</style><h1>{title}</h1><p>Pumpkin Patch · {d['size']:g} cm target width · {html.escape(b['name'])}</p><button onclick="print()">Print guide</button><h2>Gather your tools</h2><p>Washable marker, tape, pin, scoop, pumpkin saw, and a battery LED candle.</p><ol><li>Wash and dry your pumpkin. Choose a flat side for the face.</li><li>An adult should cut an angled lid with a small alignment notch. Scoop out the pulp and thin the face evenly to about 2–3 cm.</li><li>Tape the template to the pumpkin. Snip the paper edges to fit the curve. Prick along the dark boundaries, remove the paper and connect the dots.</li><li>Cut the dark regions, starting with the smallest shapes. Leave white teeth and bridges intact. Use short saw strokes and keep your free hand away from the blade.</li><li>Put a battery LED inside, replace the lid, and enjoy your pumpkin.</li></ol><p>Children need adult help with cutting. Digital geometry is stylized: widen fragile bridges and adjust the design to your real pumpkin. Use an LED to avoid heat and flame.</p><section class="pattern"><h2>Carving pattern</h2><p>Cut dark areas. Keep white teeth and bridges.</p><svg xmlns="http://www.w3.org/2000/svg" width="{width*scale:.1f}mm" height="{height*scale:.1f}mm" viewBox="0 0 200 200" preserveAspectRatio="none"><ellipse cx="100" cy="100" rx="98" ry="98" fill="none" stroke="#aaa" stroke-dasharray="2 2" stroke-width=".5"/>{svgpolys(cuts,'#222')}{svgpolys(teeth,'white')}</svg><p>Print at 100%. Pattern is {scale*100:.1f}% of target size, {width*scale/10:.1f} × {height*scale/10:.1f} cm.<br>{'Enlarge by '+str(round(100/scale))+'% for the target size.' if scale<1 else ''} Flat projection; adjust to the pumpkin curvature.</p><svg xmlns="http://www.w3.org/2000/svg" width="50mm" height="10mm" viewBox="0 0 50 10"><path d="M0 0V5H50V0" stroke="black" fill="none"/><text x="25" y="9" font-size="3" text-anchor="middle">5 cm calibration</text></svg></section></html>'''

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kw):super().__init__(*args,directory=str(ROOT/'web'),**kw)
    def log_message(self,*args):pass
    def send(self,value,status=200,ctype='application/json'):
        payload=json.dumps(value).encode() if ctype=='application/json' else value
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(payload)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/library':return self.send(dict(library=LIBRARY,default=default_design(),token=TOKEN))
        if path=='/api/gallery':
            DATA.mkdir(parents=True,exist_ok=True);entries=[]
            for p in DATA.glob('*.json'):
                try:entries.append(validate(json.loads(p.read_text())))
                except (ValueError,OSError,KeyError,TypeError):continue
            return self.send(entries)
        if path.startswith('/api/'):return self.send({'error':'Not found'},404)
        super().do_GET()
    def do_POST(self):
        if self.headers.get('X-Pumpkin-Token')!=TOKEN:return self.send({'error':'Unauthorized'},403)
        origin=self.headers.get('Origin')
        if origin and origin!=f'http://127.0.0.1:{self.server.server_port}':return self.send({'error':'Invalid origin'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>2_000_000:raise ValueError('Design file too large')
            raw=json.loads(self.rfile.read(length));path=urlparse(self.path).path
            if path=='/api/delete':
                id=raw.get('id','')
                if not re.fullmatch('[a-f0-9]{32}',id):raise ValueError('Invalid ID')
                (DATA/(id+'.json')).unlink(missing_ok=True);return self.send({'ok':True})
            d=validate(raw)
            if path=='/api/model':return self.send(packed(d))
            if path=='/api/save':
                d['id']=d['id'] or uuid.uuid4().hex;DATA.mkdir(parents=True,exist_ok=True)
                temp=DATA/(d['id']+'.tmp');temp.write_text(json.dumps(d,indent=2));temp.replace(DATA/(d['id']+'.json'));return self.send(d)
            if path=='/api/export':
                with tempfile.TemporaryDirectory() as tmp:
                    p=Path(tmp)/'pumpkin.glb';export(d,p);return self.send(p.read_bytes(),ctype='model/gltf-binary')
            if path=='/api/guide':return self.send(write_guide(d).encode(),ctype='text/html; charset=utf-8')
            if path=='/api/validate':return self.send(d)
            self.send({'error':'Not found'},404)
        except (ValueError,TypeError,KeyError,OverflowError) as e:self.send({'error':str(e)},400)
        except OSError as e:self.send({'error':'File operation failed: '+str(e)},500)

def start(port=0):
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();return server
if __name__=='__main__':
    s=start(int(sys.argv[1]) if len(sys.argv)>1 else 8765);print(f'Pumpkin Patch: http://127.0.0.1:{s.server_port}',flush=True)
    try:threading.Event().wait()
    except KeyboardInterrupt:s.shutdown()
