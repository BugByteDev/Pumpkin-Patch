import json,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from library import default_design
from mesh import export

class ExportStyleTests(unittest.TestCase):
    def load(self,path):
        raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);start=20+length
        binary=raw[start+8:]
        def accessor(index):
            a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0)
            width={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']]
            return np.frombuffer(binary,dtype=dtype,count=a['count']*width,offset=offset).reshape(a['count'],width)
        return doc,accessor
    def test_portable_colors_normals_indices_and_actual_diameter(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'styled.glb';d=default_design();d['parts']['mouth']['feature']='big';d['parts']['teeth']['feature']='buck';export(d,path)
            doc,read=self.load(path);self.assertIn('KHR_materials_unlit',doc['extensionsUsed'])
            ranges=[];has_dark_interior=False
            for mesh in doc['meshes']:
                p=mesh['primitives'][0];a=p['attributes'];position=read(a['POSITION']);normal=read(a['NORMAL']);indices=np.concatenate([read(q['indices']).flatten() for q in mesh['primitives']]);color=np.array([doc['materials'][q['material']]['pbrMetallicRoughness']['baseColorFactor'][:3] for q in mesh['primitives']])
                self.assertEqual(len(position),len(normal));self.assertNotIn('COLOR_0',a);self.assertLess(int(indices.max()),len(position))
                self.assertEqual(len(indices)%3,0);self.assertTrue(np.isfinite(color).all());self.assertTrue(((color>=0)&(color<=1)).all())
                np.testing.assert_allclose(np.linalg.norm(normal,axis=1),1,atol=1e-6)
                material=doc['materials'][p['material']];self.assertIn('KHR_materials_unlit',material['extensions']);self.assertFalse(np.allclose(material['pbrMetallicRoughness']['baseColorFactor'][:3],[1,1,1]))
                if mesh['name'] in ('body','lid'):ranges.append((position[:,0].min(),position[:,0].max()))
                srgb=np.array([93,30,0])/255;linear=np.where(srgb<=.04045,srgb/12.92,((srgb+.055)/1.055)**2.4)
                has_dark_interior|=bool(np.any(np.all(np.isclose(color,linear,atol=1e-6),axis=1)))
            self.assertTrue(has_dark_interior);self.assertAlmostEqual(max(b for a,b in ranges)-min(a for a,b in ranges),d['size']/100,places=5)
    def test_lit_export_keeps_wick_and_flame_with_baked_colors(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'lit.glb';d=default_design();d['lit']=True;export(d,path);doc,read=self.load(path)
            names={mesh['name'] for mesh in doc['meshes']};self.assertTrue({'candle','wick','flame'}<=names)
            for mesh in doc['meshes']:
                for primitive in mesh['primitives']:
                    self.assertNotIn('COLOR_0',primitive['attributes'])
                    rgb=doc['materials'][primitive['material']]['pbrMetallicRoughness']['baseColorFactor'][:3]
                    self.assertFalse(np.allclose(rgb,[1,1,1]))

    def test_color_boundary_clipping_preserves_the_surface(self):
        from mesh import build
        from export_style import split_color_boundaries
        d=default_design();d['lit']=True
        def measures(part):
            t=np.asarray(part.vertices)[np.asarray(part.faces)]
            return np.array([np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1).sum()/2,np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6])
        for part in build(d,48,32):
            before=measures(part);split_color_boundaries(part,d)
            np.testing.assert_allclose(measures(part),before,atol=1e-8,rtol=1e-8)
            c=np.asarray(part.colors)[np.asarray(part.faces)]
            self.assertTrue(np.all(c==c[:,0,None]))
