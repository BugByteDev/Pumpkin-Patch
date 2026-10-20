"""Controller tests run offscreen; they do not operate the user's desktop."""
import os,tempfile,unittest
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
import native
from library import default_design

class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=native.DATA;native.DATA=Path(self.tmp.name);self.window=native.Patch()
    def tearDown(self):
        self.window.delay.stop();self.window.pool.shutdown(wait=True,cancel_futures=True);self.window.deleteLater();native.DATA=self.old;self.tmp.cleanup()
    def test_new_pumpkins_start_without_any_facial_features(self):
        w=self.window
        self.assertTrue(all(p['feature'] is None for p in w.d['parts'].values()))
        w.set_category('eyes');w.choose('triangle');w.new()
        self.assertTrue(all(p['feature'] is None for p in w.d['parts'].values()))
        self.assertEqual(w.d['cuts'],[])
        w.undo();self.assertEqual(w.d['parts']['eyeL']['feature'],'triangle')
    def test_blank_defaults_do_not_erase_saved_faces(self):
        import json
        w=self.window;w.set_category('mouths');w.choose('grin');w.save()
        stored=native.validate(json.loads((native.DATA/(w.d['id']+'.json')).read_text()))
        self.assertEqual(stored['parts']['mouth']['feature'],'grin')
    def test_linked_removal_and_undo(self):
        w=self.window;w.set_category('eyes');w.choose('tiny');w.choose(None)
        self.assertIsNone(w.d['parts']['eyeL']['feature']);self.assertIsNone(w.d['parts']['eyeR']['feature'])
        w.undo();self.assertEqual(w.d['parts']['eyeL']['feature'],'tiny')
    def test_unlinked_independence(self):
        w=self.window;w.set_category('eyes');w.linked=False;w.choose('round');self.assertEqual(w.d['parts']['eyeL']['feature'],'round');self.assertIsNone(w.d['parts']['eyeR']['feature'])
    def test_optional_lid_and_stem(self):
        w=self.window;w.set_category('lids');w.choose(None);self.assertIsNone(w.d['lid']);w.set_category('stems');w.choose(None);self.assertIsNone(w.d['stem'])
    def test_gallery_save_and_editable_roundtrip(self):
        w=self.window;w.save();path=native.DATA/(w.d['id']+'.json');self.assertTrue(path.exists())
        import json
        self.assertEqual(native.validate(json.loads(path.read_text())),w.d)
    def test_explicit_file_saves_reveal_completed_files(self):
        from unittest.mock import patch
        w=self.window
        with patch('native.reveal_file',return_value=True) as reveal:
            for method,suffix in [(w.save_file,'.pumpkin'),(w.guide,'.html')]:
                target=str(Path(self.tmp.name)/('my pumpkin'+suffix))
                with patch.object(w,'pick_save',return_value=target):method()
                self.assertTrue(Path(target).is_file());reveal.assert_called_with(target)
    def test_cancelled_save_does_not_open_finder(self):
        from unittest.mock import patch
        with patch.object(self.window,'pick_save',return_value=''),patch('native.reveal_file') as reveal:
            self.window.save_file();self.window.export_glb();self.window.guide();reveal.assert_not_called()
    def test_failed_export_does_not_open_finder(self):
        from unittest.mock import patch
        with patch.object(self.window,'pick_save',return_value=str(Path(self.tmp.name)/'test.glb')),patch('native.export',side_effect=OSError('disk full')),patch('native.reveal_file') as reveal,patch('native.QMessageBox.warning'):
            self.window.export_glb();reveal.assert_not_called()
    def test_export_defaults_to_documents_and_reveals_real_glb(self):
        from unittest.mock import patch
        docs=Path(self.tmp.name)/'Documents';docs.mkdir();target=docs/'Pummy The Dummy.glb';self.window.d['name']='Pummy The Dummy'
        with patch('native.QStandardPaths.writableLocation',return_value=str(docs)),patch('native.QFileDialog.getSaveFileName',return_value=(str(target),'Binary glTF (*.glb)')) as dialog,patch('native.reveal_file',return_value=True) as reveal:
            self.window.export_glb()
        self.assertEqual(dialog.call_args.args[2],str(target));self.assertEqual(target.read_bytes()[:4],b'glTF');reveal.assert_called_once_with(str(target))
        self.assertEqual(self.window.save_folder(),docs.resolve())
    def test_save_filename_cannot_override_the_default_folder(self):
        from unittest.mock import patch
        docs=Path(self.tmp.name);self.window.d['name']='/Pummy/../Dummy'
        with patch.object(self.window,'save_folder',return_value=docs),patch('native.QFileDialog.getSaveFileName',return_value=('chosen.glb','')) as dialog:
            chosen=self.window.pick_save('.glb','GLB')
        self.assertEqual(Path(dialog.call_args.args[2]).parent,docs);self.assertEqual(chosen,str(docs/'chosen.glb'))
    def test_root_destination_is_rejected_before_export(self):
        from unittest.mock import patch
        with patch('native.QFileDialog.getSaveFileName',return_value=('/Pummy The Dummy.glb','')),patch('native.export') as export:
            self.window.export_glb();export.assert_not_called()
        self.assertIn('writable folder',self.window.message)

    def test_all_presets_validate(self):
        for i in range(native.PRESET_COUNT):native.validate(native.preset(i))
    def test_tools_and_teeth_removal(self):
        w=self.window;w.set_category('mouths');w.choose('big');w.set_category('teeth');w.choose('buck');w.tool('carve');self.assertEqual(w.view.mode,'carve');w.tool('carve');self.assertEqual(w.view.mode,'orbit');w.set_category('teeth');w.choose(None);self.assertIsNone(w.d['parts']['teeth']['feature']);self.assertEqual(w.d['parts']['mouth']['feature'],'big')

if __name__=='__main__':unittest.main()
