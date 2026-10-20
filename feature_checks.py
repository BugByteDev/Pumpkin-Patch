"""Exercise real widget mouse/key events in an isolated compiled-app session."""
import copy,hashlib,json,math
from pathlib import Path
import numpy as np
from PySide6.QtCore import QCoreApplication,QEvent,QPoint,QPointF,Qt
from PySide6.QtGui import QMouseEvent,QWheelEvent,QKeyEvent

class WidgetInput:
    @staticmethod
    def mouseClick(widget,button,pos):
        for kind,buttons in ((QEvent.MouseButtonPress,button),(QEvent.MouseButtonRelease,Qt.NoButton)):
            QCoreApplication.sendEvent(widget,QMouseEvent(kind,QPointF(pos),QPointF(widget.mapToGlobal(pos)),button,buttons,Qt.NoModifier))
    @staticmethod
    def keyClick(widget,key,text=''):
        for kind in (QEvent.KeyPress,QEvent.KeyRelease):QCoreApplication.sendEvent(widget,QKeyEvent(kind,key,Qt.NoModifier,text))
    @staticmethod
    def keyClicks(widget,text):
        for character in text:WidgetInput.keyClick(widget,ord(character.upper()),character)


class FeatureChecks:
    def __init__(self,window,output,result):
        self.w=window;self.output=Path(output);self.result=result;self.stage=0;self.preset_index=0
    def record(self,text):self.result['checks'].append(text)
    def click(self,label):
        import native
        piece=any(f['name'].casefold()==label.casefold() for f in native.LIBRARY[self.w.category])
        for attempt in range(20):
            self.w.repaint()
            exact=[rect for rect,fn,name in self.w.hits if name.casefold()==label.casefold()]
            matches=exact or ([] if piece else [rect for rect,fn,name in self.w.hits if label.casefold() in name.casefold()])
            if matches:
                WidgetInput.mouseClick(self.w,Qt.LeftButton,pos=matches[-1].center().toPoint());return
            # Scroll the actual feature shop when the requested piece is below it.
            point=self.w.choice_rect.center().toPoint();old=self.w.library_scroll
            QCoreApplication.sendEvent(self.w,QWheelEvent(QPointF(point),QPointF(self.w.mapToGlobal(point)),QPoint(),QPoint(0,-120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False))
            if self.w.library_scroll==old:break
        raise AssertionError('Control not visible: '+label)
    def panel_click(self,action,index=None):
        panel=self.w.overlay;panel.repaint()
        matches=[rect for rect,a,i in panel.hits if a==action and (index is None or i==index)]
        assert matches,'Panel control not visible: '+action
        WidgetInput.mouseClick(panel,Qt.LeftButton,pos=matches[-1].center().toPoint())
    def drag(self,widget,points):
        for i,point in enumerate(points):
            point=QPoint(*map(round,point));kind=QEvent.MouseButtonPress if i==0 else QEvent.MouseButtonRelease if i==len(points)-1 else QEvent.MouseMove
            button=Qt.NoButton if kind==QEvent.MouseMove else Qt.LeftButton
            buttons=Qt.NoButton if kind==QEvent.MouseButtonRelease else Qt.LeftButton
            QCoreApplication.sendEvent(widget,QMouseEvent(kind,QPointF(point),QPointF(widget.mapToGlobal(point)),button,buttons,Qt.NoModifier))
    def frame_hash(self):
        frame=self.w.view.grabFramebuffer()
        return hashlib.sha256(bytes(frame.constBits())).hexdigest()
    def volume(self):
        from model_cache import build_cached
        total=0
        for part in build_cached(self.w.d):
            t=np.asarray(part.vertices)[np.asarray(part.faces)]
            total+=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
        return total
    def file_action(self,label,path):
        import native
        save=native.QFileDialog.getSaveFileName;open_=native.QFileDialog.getOpenFileName;reveal=native.reveal_file
        try:
            native.QFileDialog.getSaveFileName=lambda *a,**k:(str(path),'')
            native.QFileDialog.getOpenFileName=lambda *a,**k:(str(path),'')
            native.reveal_file=lambda p:True
            self.click(label)
        finally:
            native.QFileDialog.getSaveFileName=save;native.QFileDialog.getOpenFileName=open_;native.reveal_file=reveal
    def tick(self):
        w=self.w;view=w.view
        if self.stage==0:
            self.click('new pumpkin');assert all(p['feature'] is None for p in w.d['parts'].values())
            self.click('eyes');self.click('Classic triangle')
            assert w.d['parts']['eyeL']['feature']==w.d['parts']['eyeR']['feature']=='triangle'
            self.click('× remove');assert all(w.d['parts'][s]['feature'] is None for s in ('eyeL','eyeR'))
            self.click('↶ undo');assert w.d['parts']['eyeR']['feature']=='triangle'
            self.click('link pair');self.click('× remove')
            assert w.d['parts']['eyeL']['feature'] is None and w.d['parts']['eyeR']['feature']=='triangle'
            self.record('mouse clicks: blank new pumpkin, linked eyes, removal, undo and independent eyes')
        elif self.stage==1:
            self.base_volume=self.volume()
            self.click('freehand carver');self.click('mirror cuts')
            assert view.mode=='carve' and view.mirror
            width,height=view.width(),view.height();corners=[(.36,.47),(.44,.47),(.44,.58),(.36,.58),(.36,.47)]
            points=[]
            for a,b in zip(corners,corners[1:]):
                points.extend(((a[0]+(b[0]-a[0])*t/10)*width,(a[1]+(b[1]-a[1])*t/10)*height) for t in range(10))
            points.append((corners[-1][0]*width,corners[-1][1]*height));self.drag(view,points)
            assert len(w.d['cuts'])==2,'Mouse-drawn mirrored cut was not created'
            left,right=w.d['cuts'];assert right==[[-x,y] for x,y in reversed(left)]
            self.carved=copy.deepcopy(w.d['cuts'])
        elif self.stage==2:
            assert self.volume()<self.base_volume,'Carving did not remove actual pumpkin volume'
            self.click('undo cut');assert not w.d['cuts']
            self.click('↶ undo');assert w.d['cuts']==self.carved
            self.click('↷ redo');assert not w.d['cuts']
            self.click('↶ undo');assert w.d['cuts']==self.carved
            self.record('mouse-drawn stabilized mirror carving removes volume; undo cut, undo and redo restore the expected geometry')
            self.click('freehand carver');assert view.mode=='orbit'
            self.old_yaw=view.yaw;self.old_pitch=view.pitch;self.old_frame=self.frame_hash()
            x,y=view.width()/2,view.height()/2;self.drag(view,[(x,y),(x+25,y+12),(x+50,y+25),(x+50,y+25)])
            assert view.yaw!=self.old_yaw and view.pitch!=self.old_pitch
        elif self.stage==3:
            assert self.frame_hash()!=self.old_frame,'Rotation did not change the rendered pumpkin'
            old=view.distance;point=view.rect().center()
            QCoreApplication.sendEvent(view,QWheelEvent(QPointF(point),QPointF(view.mapToGlobal(point)),QPoint(),QPoint(0,120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False))
            assert view.distance<old
            self.click('front view');assert view.yaw==view.pitch==0
            self.record('mouse drag rotates the visible pumpkin; wheel zoom and front view work')
            self.click('body');self.click('Tall');assert w.d['body']=='tall'
            self.click('stem');self.click('None / remove');assert w.d['stem'] is None
            self.click('lid');self.click('None / remove');assert w.d['lid'] is None
        elif self.stage==4:
            names={obj['name'] for obj in view.objects}
            assert 'stem' not in names and 'lid' not in names
            self.record('body selection changes the shape; removed stem and lid are absent from the rendered mesh')
            self.click('↶ undo');self.click('↶ undo');self.click('whole faces');self.click('Razor grin')
            assert w.d['name']=='Razor grin'
            self.preset_index=0
        elif self.stage==5:
            import native
            if self.preset_index<native.PRESET_COUNT:
                w.apply_preset(self.preset_index);self.preset_index+=1;return False
            self.record(str(native.PRESET_COUNT)+' complete face presets rendered without a build or graphics error')
            self.click('Light it up');assert w.busy and w.d['lit'] and view.anim is not None
        elif self.stage==6:
            if w.busy or view.anim is not None:return False
            assert w.name.isEnabled() and w.d['lit']
            w.grab().save(str(self.output/'completed.png'))
            self.record('Complete button finishes lid/candle animation and returns to an editable lit pumpkin')
            w.name.selectAll();WidgetInput.keyClicks(w.name,'Feature test pumpkin');assert w.d['name']=='Feature test pumpkin'
            self.saved=copy.deepcopy(w.d);self.path=self.output/'feature-roundtrip.pumpkin'
            self.file_action('save file',self.path);assert json.loads(self.path.read_text())==self.saved
            w.name.selectAll();WidgetInput.keyClicks(w.name,'Changed name');self.file_action('open file',self.path)
            assert w.d==self.saved
        elif self.stage==7:
            self.record('typed name, Save file and Open file preserve the full pumpkin design')
            glb=self.output/'feature-export.glb';guide=self.output/'feature-guide.html'
            self.file_action('export .glb',glb);assert glb.read_bytes()[:4]==b'glTF'
            self.file_action('carving guide',guide);assert 'Feature test pumpkin' in guide.read_text() and '5 cm calibration' in guide.read_text()
            self.record('Export GLB and Carving guide buttons create the expected files')
            self.click('save to my patch');self.gallery_id=w.d['id'];self.saved=copy.deepcopy(w.d)
            self.click('new pumpkin');self.click('my pumpkins')
            self.index=next(i for i,(_,d) in enumerate(w.overlay.items) if d['id']==self.gallery_id)
            self.panel_click('open',self.index);assert w.d==self.saved
        elif self.stage==8:
            self.record('saved pumpkin reopens from the gallery with its name and design intact')
            self.click('my pumpkins');self.index=next(i for i,(_,d) in enumerate(w.overlay.items) if d['id']==self.gallery_id)
            path=w.overlay.items[self.index][0]
            self.panel_click('delete',self.index);self.panel_click('cancel',self.index);assert path.exists()
            self.panel_click('delete',self.index);self.panel_click('confirm',self.index);assert not path.exists()
            self.panel_click('close');self.record('gallery deletion can be cancelled and requires confirmation')
            self.click('?')
            import panels
            opened=[];original=panels.QDesktopServices.openUrl
            try:
                panels.QDesktopServices.openUrl=lambda url:opened.append(url.toString()) or True
                self.panel_click('repository')
            finally:panels.QDesktopServices.openUrl=original
            assert opened==['https://github.com/BugByteDev/Pumpkin-Patch']
            WidgetInput.keyClick(w.overlay,Qt.Key_Escape);assert w.overlay is None
            self.record('Info repository button hands the correct URL to the browser; Escape closes Info')
            return True
        self.stage+=1
        return False
