import collections,copy,json,math,os,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from library import LIBRARY,default_design,face_polygons
from mesh import build,export,surface,body_info
from storage import validate,write_guide
import manifold3d as m
import numpy as np

def manifold(part):
    # Crease normals intentionally split vertices; weld only for topology checks.
    unique={};vertices=[];ids=[]
    for p in part.vertices:
        key=tuple(round(v,6) for v in p)
        if key not in unique:unique[key]=len(vertices);vertices.append(p)
        ids.append(unique[key])
    faces=[[ids[i] for i in f] for f in part.faces]
    return m.Manifold(m.Mesh(np.array(vertices,dtype=np.float32),np.array(faces,dtype=np.uint32)))

def carved_design():
    d=default_design()
    for key in ('eyeL','eyeR'):d['parts'][key]['feature']='tiny'
    d['parts']['mouth']['feature']='big';d['parts']['teeth']['feature']='buck'
    return d

class GeometryTests(unittest.TestCase):
    def assertSolid(self,p):
        shape=manifold(p)
        self.assertEqual(shape.status(),m.Error.NoError,p.name)
        self.assertGreater(shape.volume(),0,p.name)
        self.assertTrue(all(math.isfinite(v) for point in p.vertices for v in point))
    def test_carved_design_has_actual_openings_and_closed_parts(self):
        d=carved_design();parts=build(d)
        for p in parts:self.assertSolid(p)
        body=next(p for p in parts if p.name=='body')
        ray=m.Manifold.ray_cast if hasattr(m.Manifold,'ray_cast') else None
        # The opening is represented by vertices on its exact boundary, not raster steps.
        self.assertTrue(any(abs(v[0]-.59*body_info(d)['sx'])<1e-5 for v in body.vertices))
    def test_classic_has_pumpkin_proportions_and_lobes(self):
        body=body_info(carved_design())
        points=[surface(i*math.tau/128,j*math.pi/80,body) for i in range(128) for j in range(81)]
        width=max(p[0] for p in points)-min(p[0] for p in points)
        height=max(p[1] for p in points)-min(p[1] for p in points)
        self.assertGreater(width/height,1.20)
        peak=surface(0,math.pi/2,body)[2]
        valley=math.hypot(*[surface(math.pi/body['ribs'],math.pi/2,body)[k] for k in (0,2)])
        self.assertGreater(peak-valley,.10)
        self.assertLess(peak-valley,.16)
        self.assertLess(surface(0,0,body)[1],surface(0,.3,body)[1])

    def test_every_body(self):
        for b in LIBRARY['bodies']:
            d=carved_design();d['body']=b['id']
            for part in build(d,96,64):self.assertSolid(part)
    def test_all_mouth_styles(self):
        for f in LIBRARY['mouths']:
            d=carved_design();d['parts']['mouth']['feature']=f['id']
            for p in build(d,96,64):self.assertSolid(p)
    def test_each_teeth_style(self):
        for t in LIBRARY['teeth']:
            d=carved_design();d['parts']['teeth']['feature']=t['id']
            body=next(p for p in build(d) if p.name=='body');self.assertSolid(body)
            self.assertEqual(len(manifold(body).decompose()),1,t['name'])
    def test_remove_all_optional_parts(self):
        d=carved_design();d['stem']=None;d['lid']=None
        for p in d['parts'].values():p['feature']=None
        self.assertEqual(face_polygons(d),([],[]))
        parts=build(d);self.assertNotIn('lid',[p.name for p in parts]);self.assertNotIn('stem',[p.name for p in parts])
        for p in parts:self.assertSolid(p)
    def test_rotation_and_asymmetric_parts(self):
        d=carved_design();d['parts']['eyeL'].update(feature='round',rotation=32,x=-.41,sx=.21,sy=.1);d['parts']['eyeR']['feature']=None
        for p in build(d):self.assertSolid(p)
    def test_custom_cut_can_remove_the_center_of_a_preset_tooth(self):
        d=default_design();d['parts']['mouth']['feature']='big';d['parts']['teeth']['feature']='buck'
        b=body_info(d);x=-.07375;y=.36
        ray=((x*b['sx'],(y+1)*b['sy'],3*b['sx']),(x*b['sx'],(y+1)*b['sy'],0))
        def hits():
            body=next(p for p in build(d) if p.name=='body')
            return manifold(body).ray_cast(*ray)
        self.assertGreater(len(hits()),0)
        d['cuts']=[[[-.11,.31],[-.04,.31],[-.04,.40],[-.11,.40]]]
        self.assertEqual(len(hits()),0)

    def test_custom_cut(self):
        d=carved_design();d['cuts']=[[[-.8,-.1],[-.67,.12],[-.55,-.08],[-.7,-.2]]]
        cut_volume=sum(manifold(p).volume() for p in build(d))
        d['cuts']=[];base_volume=sum(manifold(p).volume() for p in build(d))
        self.assertLess(cut_volume,base_volume)
    def test_round_eye_contains_curved_boundary(self):
        d=carved_design();d['parts']['eyeL'].update(feature='round',sx=.18,sy=.18,x=-.32,y=.61)
        body=next(p for p in build(d) if p.name=='lid')
        xs={round(p[0],5) for p in body.vertices if -.51<p[0]<-.12 and 1.4<p[1]<1.85 and p[2]>.1}
        self.assertGreater(len(xs),20)
    def test_glb_layout_and_units(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=carved_design();p=Path(tmp)/'test.glb';export(d,p);raw=p.read_bytes()
            magic,version,size=struct.unpack_from('<III',raw);self.assertEqual((magic,version,size),(0x46546c67,2,len(raw)))
            length,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+length])
            self.assertEqual(doc['asset']['version'],'2.0');self.assertEqual(doc['extras']['units'],'metres')
            self.assertNotIn('candle',[p['name'] for p in doc['meshes']])
            self.assertLess(max(a['max'][0] for a in doc['accessors'] if 'max' in a),.20)
            d['lit']=True;export(d,p);raw=p.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);self.assertIn('flame',[p['name'] for p in doc['meshes']])

class DataTests(unittest.TestCase):
    def test_library_counts(self):
        self.assertGreaterEqual(len(LIBRARY['mouths']),84);self.assertGreaterEqual(len(LIBRARY['eyes']),36)
        for key,features in LIBRARY.items():self.assertEqual(len(features),len({p['id'] for p in features}),key)
    def test_roundtrip_and_validation(self):
        d=default_design();self.assertEqual(validate(json.loads(json.dumps(d))),d)
        for key,value in [('size',float('nan')),('body','unknown'),('color','#ffffff'),('id','../../tmp')]:
            bad=copy.deepcopy(d);bad[key]=value
            with self.assertRaises(ValueError):validate(bad)
    def test_guide_escapes_name_and_includes_real_pattern(self):
        d=carved_design();d['name']='<script>alert(1)</script>';guide=write_guide(d)
        self.assertNotIn('<script>',guide);self.assertIn('&lt;script&gt;',guide);self.assertIn('5 cm calibration',guide);self.assertIn('polygon',guide)

if __name__=='__main__':unittest.main(verbosity=2)
