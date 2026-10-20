import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import model_cache,thumbnails
from library import default_design
from legacy_mesh import Part
from PySide6.QtGui import QImage,QColor

class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=model_cache.DATA;model_cache.DATA=Path(self.temp.name)
        model_cache._memory.clear();thumbnails._cache.clear()
    def tearDown(self):
        model_cache.DATA=self.old;model_cache._memory.clear();thumbnails._cache.clear();self.temp.cleanup()
    def test_geometry_survives_restart_and_ignores_rename_color_light(self):
        d=default_design();p=Part('body',[(0,0,0),(1,0,0),(0,1,0)],[(0,1,2)],(1,.5,0));p.normals=[(0,0,1)]*3
        with patch('model_cache.build',return_value=[p]) as build,patch('model_cache.can_write',return_value=True):
            model_cache.cache_dir('meshes').mkdir(parents=True,exist_ok=True)
            model_cache.build_cached(d);self.assertEqual(build.call_count,1)
            model_cache._memory.clear()
            d.update(name='Renamed',id='saved',lit=True,color='#ff5200')
            result=model_cache.build_cached(d);self.assertEqual(build.call_count,1)
            self.assertEqual(result[0].color,(1,82/255,0))
            d['parts']['mouth']['feature']='snarl';model_cache.build_cached(d)
            self.assertEqual(build.call_count,2)
    def test_disk_preview_loads_without_render_and_edits_invalidate(self):
        d=default_design();key=model_cache.signature(d,image=True)
        path=model_cache.cache_dir('previews')/(key+'.png');path.parent.mkdir(parents=True)
        image=QImage(10,10,QImage.Format_RGBA8888);image.fill(QColor('#ff8200'));self.assertTrue(image.save(str(path)))
        with patch('thumbnails._pool.submit') as submit:
            self.assertIsNotNone(thumbnails.preview(d));thumbnails._cache.clear()
            d['name']='Another name';self.assertIsNotNone(thumbnails.preview(d));submit.assert_not_called()
            d['parts']['eyeL']['feature']='demon';thumbnails.preview(d);submit.assert_called_once()
    def test_corrupt_mesh_cache_rebuilds(self):
        d=default_design();key=model_cache.signature(d)+'-96x64';path=model_cache.cache_dir('meshes')/(key+'.json.gz')
        path.parent.mkdir(parents=True);path.write_bytes(b'broken')
        with patch('model_cache.build',return_value=[]) as build:
            self.assertEqual(model_cache.build_cached(d),[]);build.assert_called_once()
