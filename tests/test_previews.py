import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import manifold3d as m
from library import LIBRARY,default_design
from mesh import stem_part,body_info
from thumbnails import render

class PreviewTests(unittest.TestCase):
    def test_every_stem_is_a_closed_positive_volume_mesh(self):
        body=body_info(default_design())
        for style in LIBRARY['stems']:
            with self.subTest(stem=style['id']):
                part=stem_part(style['id'],body)
                solid=m.Manifold(m.Mesh(np.asarray(part.vertices,dtype=np.float32),np.asarray(part.faces,dtype=np.uint32)))
                self.assertEqual(solid.status(),m.Error.NoError)
                self.assertGreater(solid.volume(),0)
    def test_preview_uses_actual_cuts_and_removed_stem(self):
        d=default_design();d['stem']=None
        plain=render(d,100,100)
        d['cuts']=[[[-.35,.3],[.35,.3],[.35,-.3],[-.35,-.3]]]
        carved=render(d,100,100)
        self.assertNotEqual(bytes(plain.constBits()),bytes(carved.constBits()))
        self.assertGreater(carved.pixelColor(50,50).alpha(),0)
        self.assertEqual(carved.pixelColor(0,0).alpha(),0)
