import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
import native,panels

class PanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=native.DATA;native.DATA=Path(self.temp.name);self.w=native.Patch();self.w.delay.stop()
    def tearDown(self):
        self.w.delay.stop();self.w.poll.stop();self.w.pool.shutdown(wait=False,cancel_futures=True);self.w.deleteLater();native.DATA=self.old;self.temp.cleanup()
    def test_info_and_gallery_are_child_panels_not_windows(self):
        for open_page in (self.w.help,self.w.gallery):
            with patch('panels.DATA',Path(self.temp.name)):open_page()
            page=self.w.overlay;self.assertIs(page.parent(),self.w);self.assertFalse(page.isWindow());self.assertIs(page.window(),self.w)
            self.assertTrue(self.w.view.isHidden());self.w.close_overlay();self.assertIsNone(self.w.overlay)
    def test_failed_autosave_does_not_prevent_startup_or_editing(self):
        with patch.object(Path,'write_text',side_effect=OSError('No space left')):
            self.w.changed();self.assertIn('Could not autosave',self.w.message)
        self.w.delay.stop();self.w.apply_preset(24);self.w.delay.stop();self.assertEqual(self.w.d['name'],'Razor grin')
    def test_failed_preview_cannot_escape_a_paint_callback(self):
        import thumbnails
        from concurrent.futures import Future
        from model_cache import signature
        d=native.default_design();key=signature(d,image=True);future=Future();future.set_exception(RuntimeError('worker failed'))
        thumbnails._cache[key]=future
        image=thumbnails.preview(d);self.assertFalse(image.isNull());thumbnails._cache.pop(key)
