"""Native Python UI: every visible app control is drawn with QPainter.
No HTML, CSS, JavaScript, browser engine, or HTTP server is used by this entry point.
"""
import copy,json,math,os,re,sys,time,uuid
from workers import WorkPool,build_model
from pathlib import Path
from PySide6.QtCore import Qt,QRectF,QPointF,QTimer,QStandardPaths
from PySide6.QtGui import QPainter,QPainterPath,QColor,QPen,QFont,QFontDatabase,QPolygonF,QSurfaceFormat,QKeySequence,QShortcut,QFontMetricsF,QIcon
from PySide6.QtWidgets import QApplication,QWidget,QLineEdit,QFileDialog,QMessageBox,QMenu,QDialog,QVBoxLayout,QTextEdit
from library import LIBRARY,PART_LIBRARY,default_design,face_polygons
from mesh import build,export
from model_cache import build_cached
from storage import validate,write_guide,DATA
from renderer import PumpkinView
from file_reveal import reveal_file
from thumbnails import preview,shutdown_previews
from scary_faces import scary_preset,SCARY_FACES
PRESET_COUNT=24+len(SCARY_FACES)
PRESET_ORDER=list(range(24,PRESET_COUNT))+list(range(24))
ROOT=Path(__file__).resolve().parent
Y='#ffd524';C='#fffc78';O='#ff8200';A='#ffbb0b';R='#ff5200';B='#5d1e00'
CATEGORIES=[('bodies','body'),('stems','stem'),('lids','lid'),('eyes','eyes'),('brows','brows'),('noses','nose'),('mouths','mouth'),('teeth','teeth'),('extras','extras')]
SLOTS={'eyes':['eyeL','eyeR'],'brows':['browL','browR'],'noses':['nose'],'mouths':['mouth'],'teeth':['teeth'],'extras':['extraL','extraR']}
NAMES={'eyeL':'left eye','eyeR':'right eye','browL':'left eyebrow','browR':'right eyebrow','nose':'nose','mouth':'mouth','teeth':'teeth','extraL':'left detail','extraR':'right detail'}

def font(px):
    f=QFont('Patrick Hand');f.setPixelSize(px);return f

def preset(i):
    if i>=24:return scary_preset(i-24)
    d=default_design();p=d['parts'];names=['The big laugh','Buck-tooth boo','A little gasp','Cheeky grin','Sleepy pumpkin','Happy camper','Toothy smile','Round-eyed wonder','A crooked smile','Tiny grin','Two fangs','The belly laugh','Classic jack','Cross-eyed cheer','Soft smile','Tall shout','Snaggle grin','Wide awake','Tiny teeth','Cat smile','Surprised','Wink and grin','Diamond grin','The deadpan'];d['name']=names[i]
    if i<12:
        eye=['tiny','round','tiny','happy','sleepy','happy','triangle','round','side','tiny','angry','tiny'][i];mouth=['big','big','gasp','grin','laugh','laugh','grin','big','wonky','smile','laugh','wide'][i]
        for key in ('eyeL','eyeR'):p[key].update(feature=eye,sx=.15 if i==7 else .11,sy=.15 if i==7 else .10,y=.66)
        p['mouth'].update(feature=mouth,sx=.59,sy=.35 if mouth in ('grin','smile','wonky') else .56,y=-.14)
        p['teeth']['feature']=['buck','single',None,'bottom',None,'buck','four',None,'snaggle',None,'fangs','buck'][i]
    else:
        j=i-12
        for key in ('eyeL','eyeR'):p[key].update(feature=['triangle','cross','happy','tall','round','round','tiny','happy','round','wink','diamond','sleepy'][j],sx=.16,sy=.17,y=.33)
        p['mouth'].update(feature=['grin','laugh','smile','big','wonky','grin','wide','cat','gasp','smirk','grin','flat'][j],sx=.57,sy=.29,y=-.32)
        p['nose']['feature']='triangle' if j==0 else None;p['teeth']['feature']=['four',None,None,'buck','single',None,'buck',None,None,'bottom','fangs',None][j]
        if j==9:p['eyeR']['feature']='round'
    return d

class CanvasHelpers:
    def rendered_image(self,p,image,rect):
        if image.isNull():return
        scale=min(rect.width()/image.width(),rect.height()/image.height())
        w=image.width()*scale;h=image.height()*scale
        target=QRectF(rect.center().x()-w/2,rect.center().y()-h/2,w,h)
        p.save();p.setRenderHint(QPainter.SmoothPixmapTransform);p.drawImage(target,image);p.restore()
    def txt(self,p,x,y,text,px=19,color=B):
        p.setFont(font(px));p.setPen(QColor(color));p.drawText(QPointF(x,y+px*.84),text)
    def line(self,p,points,color=B,width=2):
        p.setPen(QPen(QColor(color),width));p.setBrush(Qt.NoBrush);p.drawPolyline(QPolygonF([QPointF(*v) for v in points]))
    def panel(self,p,x,y,w,h,tape=False):
        path=QPainterPath();path.moveTo(x+6,y);path.cubicTo(x+w*.35,y-1,x+w*.70,y+1,x+w-5,y);path.quadTo(x+w,y,x+w,y+7);path.lineTo(x+w,y+h-8);path.quadTo(x+w,y+h,x+w-7,y+h);path.lineTo(x+6,y+h);path.quadTo(x,y+h,x,y+h-7);path.lineTo(x,y+7);path.quadTo(x,y,x+6,y)
        p.save();p.translate(4,5);p.fillPath(path,QColor(B));p.restore();p.fillPath(path,QColor(C));p.setPen(QPen(QColor(B),2));p.drawPath(path)
        if tape:
            p.save();p.translate(x+13,y-6);p.rotate(-6);p.fillRect(QRectF(0,0,60,18),QColor(A));p.restore()
            p.save();p.translate(x+w-65,y-7);p.rotate(8);p.fillRect(QRectF(0,0,40,16),QColor(A));p.restore()
    def poly(self,p,points,color=B):p.setPen(Qt.NoPen);p.setBrush(QColor(color));p.drawPolygon(QPolygonF([QPointF(*v) for v in points]))
    def icon(self,p,feature,cat,rect):
        if cat in ('bodies','stems'):
            d=default_design();d['body' if cat=='bodies' else 'stem']=feature['id']
            image=preview(d,stem_only=cat=='stems')
            if image is not None:self.rendered_image(p,image,rect)
            else:QTimer.singleShot(100,self.update)
            return
        p.save();p.translate(rect.center());scale=min(rect.width(),rect.height())/2.8;p.scale(scale,scale)
        if 'polygons' in feature:
            for points in feature['polygons']:self.poly(p,[(x,-y) for x,y in points])
        elif cat=='lids':
            q=QPainterPath();q.moveTo(-1,.3);q.quadTo(0,-1.2,1,.3);q.closeSubpath();p.fillPath(q,QColor(O));p.setPen(QPen(QColor(B),.04));p.drawPath(q)
        elif cat=='teeth':
            p.setPen(Qt.NoPen);p.setBrush(QColor(B));p.drawRoundedRect(QRectF(-1.1,-.85,2.2,1.7),.4,.4)
            for count,sign in ((feature['top'],1),(feature['bottom'],-1)):
                for i in range(count):
                    x=(i-(count-1)/2)*.4;y=-.88 if sign==1 else .88
                    pts=[(x-.12,y),(x+.12,y),(x,y+sign*.6)] if feature['pointed'] else [(x-.12,y),(x+.12,y),(x+.12,y+sign*.5),(x-.12,y+sign*.5)]
                    self.poly(p,pts,C)
        p.restore()
    def draw_face(self,p,d,rect):
        image=preview(d)
        if image is None:
            self.txt(p,rect.x()+8,rect.center().y(),'rendering…',14)
            QTimer.singleShot(100,self.update)
        else:self.rendered_image(p,image,rect)

class Patch(QWidget,CanvasHelpers):
    def __init__(self):
        super().__init__();self.setWindowTitle('Pumpkin Patch — Python');self.resize(1440,912);self.setMinimumSize(1080,730);self.setMouseTracking(True)
        self.overlay=None;self.d=default_design();self.category='mouths';self.slot='mouth';self.linked=True;self.right_tab='part';self.library_scroll=0;self.preset_scroll=0;self.hits=[];self.active_slider=None;self.history=[];self.future_history=[];self.message='a fresh pumpkin, a blank-ish canvas.';self.drag_start=None;self.busy=False;self.cut_groups=[]
        DATA.mkdir(parents=True,exist_ok=True);self.draft=DATA/'draft.pumpkin'
        if self.draft.exists():
            try:self.d=validate(json.loads(self.draft.read_text()))
            except (ValueError,KeyError,TypeError,OSError):pass
        self.view=PumpkinView(self);self.view.design=self.d;self.view.status.connect(self.status);self.view.carved.connect(self.add_cut);self.view.moved.connect(self.move_feature);self.view.animationDone.connect(self.finished)
        self.name=QLineEdit(self.d['name'],self);self.name.setFont(font(29));self.name.setStyleSheet('QLineEdit {background:transparent; color:#5d1e00; border:0px; border-bottom:2px solid #5d1e00; padding:0px 0px 5px 0px;}');self.name.setAccessibleName('Pumpkin name');self.name.setMaxLength(80);self.name.textEdited.connect(self.rename)
        self.pool=WorkPool();self.job=None;self.revision=0;self.want_revision=0;self.delay=QTimer(self);self.delay.setSingleShot(True);self.delay.timeout.connect(self.start_model);self.poll=QTimer(self);self.poll.timeout.connect(self.check_model);self.poll.start(45)
        self.keyboard=[]
        for keys,fn in [('Ctrl+Z',self.undo),('Ctrl+Shift+Z',self.redo),('Meta+Z',self.undo),('Meta+Shift+Z',self.redo),('Escape',lambda:self.close_overlay() if self.overlay is not None else self.tool('orbit')),('Alt+F',self.view.front),('Alt+L',self.toggle_glow)]:
            shortcut=QShortcut(QKeySequence(keys),self);shortcut.activated.connect(fn);self.keyboard.append(shortcut)
        self.changed();self.view.front()
    def status(self,text):self.message=text;self.update()
    def remember(self):
        self.history.append(copy.deepcopy(self.d));self.history=self.history[-70:];self.future_history=[]
    def changed(self,rebuild=True):
        try:
            temp=self.draft.with_suffix('.tmp');temp.write_text(json.dumps(self.d));temp.replace(self.draft)
        except OSError:self.message='Could not autosave. Your pumpkin is still open; free some space before saving.'
        self.view.design=self.d;self.view.update()
        if rebuild:self.want_revision+=1;self.delay.start(120)
        self.update()
    def start_model(self):
        if self.job is not None:return
        self.revision=self.want_revision
        try:self.job=self.pool.submit(build_model,copy.deepcopy(self.d))
        except Exception as e:self.job=None;self.status('Could not start that carving. You can keep editing: '+str(e))
    def check_model(self):
        if self.job is None:return
        if not self.job.done():return
        try:
            parts=self.job.result()
            if self.revision==self.want_revision:self.view.set_parts(parts,self.d)
        except Exception as e:self.status('Could not build that carving: '+str(e))
        self.job=None
        if self.revision!=self.want_revision:self.start_model()
    def rename(self,text):self.d['name']=text;self.changed(False)
    def refresh(self):self.cut_groups=[];self.name.setText(self.d['name']);self.changed()
    def undo(self):
        if not self.history or self.busy:return
        self.future_history.append(copy.deepcopy(self.d));self.d=self.history.pop();self.refresh()
    def redo(self):
        if not self.future_history or self.busy:return
        self.history.append(copy.deepcopy(self.d));self.d=self.future_history.pop();self.refresh()
    def layout_values(self):
        w,h=self.width(),self.height();left=292 if w>=1150 else 248;right=250 if w>=1150 else 220;gap=24 if w>=1150 else 16;padding=28 if w>=1150 else 16;top=144;bottom=h-46;mainh=bottom-top;cx=padding+left+gap;rx=w-padding-right;cw=rx-gap-cx
        return w,h,padding,left,right,gap,top,bottom,mainh,cx,rx,cw
    def resizeEvent(self,e):
        w,h,pad,l,r,g,t,b,m,cx,rx,cw=self.layout_values();self.stage_rect=QRectF(cx,t+35,cw,max(330,m-170));self.view.setGeometry(self.stage_rect.toRect());self.name.setGeometry(int(cx+70),int(b-80),int(cw-80),45)
        if self.overlay is not None:self.overlay.setGeometry(self.rect())
    def button(self,p,rect,text,fn,px=19,active=False,enabled=True):
        if active:
            p.setPen(QPen(QColor(B),1));p.setBrush(QColor(O));p.drawRoundedRect(rect,5,5)
        p.setFont(font(px));p.setPen(QColor(B if enabled else A));p.drawText(rect,Qt.AlignCenter,text)
        if enabled:self.hits.append((rect,fn,text))
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.fillRect(self.rect(),QColor(Y));self.hits=[]
        w,h,pad,l,r,g,t,b,m,cx,rx,cw=self.layout_values()
        for x in range(0,w,24):p.fillRect(QRectF(x,0,12,9),QColor(O));p.fillRect(QRectF(x,h-9,12,9),QColor(O))
        self.txt(p,30,31,'pumpkin patch',43);self.txt(p,278,43,'✳',25,R);self.txt(p,30,84,'a jack-o’-lantern maker · made to be yours',16)
        self.button(p,QRectF(w-340,43,112,36),'new pumpkin',self.new)
        self.button(p,QRectF(w-218,43,154,36),'my pumpkins ↗',self.gallery)
        p.setPen(QPen(QColor(B),2));p.setBrush(Qt.NoBrush);p.drawEllipse(QRectF(w-53,44,33,33));self.button(p,QRectF(w-53,43,33,34),'?',self.help,22)
        # Left feature browser: same geometry, font and SVG path points as the reference.
        self.panel(p,pad,t,l,m,True);x=pad+16
        self.txt(p,x,t+15,'the face shop',29);self.txt(p,x,t+59,'pick a part. make it yours.',16)
        catx=x;caty=t+96
        for cat,label in CATEGORIES:
            width=QFontMetricsF(font(17)).horizontalAdvance(label)+10
            if catx+width>pad+l-10:catx=x;caty+=31
            rect=QRectF(catx,caty,width,27);self.button(p,rect,label,lambda c=cat:self.set_category(c),17)
            if cat==self.category:self.line(p,[(catx+4,caty+26),(catx+width-4,caty+27)],R,3)
            catx+=width+4
        sep=caty+38;self.line(p,[(x,sep),(pad+l-16,sep)],O,2)
        self.txt(p,x,sep+14,'find your grin' if self.category=='mouths' else 'pick your '+dict(CATEGORIES)[self.category],22)
        self.txt(p,pad+l-76,sep+18,f'{len(LIBRARY[self.category])} styles',15)
        self.choice_top=sep+82;self.choice_bottom=b-135;self.choice_rect=QRectF(x,self.choice_top,l-32,self.choice_bottom-self.choice_top)
        if self.category in SLOTS:
            self.txt(p,x,sep+51,'editing',15);self.button(p,QRectF(x+47,sep+46,104,27),NAMES.get(self.slot,self.slot)+' ▾',self.target_menu,15)
            if len(SLOTS[self.category])==2:self.button(p,QRectF(pad+l-91,sep+46,76,27),('☑' if self.linked else '☐')+' link pair',self.toggle_link,15)
        chosen=self.d['body'] if self.category=='bodies' else self.d['stem'] if self.category=='stems' else self.d['lid'] if self.category=='lids' else self.d['parts'][self.slot]['feature']
        choices=LIBRARY[self.category] if self.category=='bodies' else [dict(id=None,name='None / remove')]+sorted(LIBRARY[self.category],key=lambda f:not f.get('scary',False));cols=4;cellw=(l-32)/cols;cellh=65
        p.save();p.setClipRect(self.choice_rect)
        for i,f in enumerate(choices):
            box=QRectF(x+i%cols*cellw,self.choice_top+i//cols*cellh-self.library_scroll,cellw-3,cellh-4)
            if not box.intersects(self.choice_rect):continue
            if chosen==f['id']:
                p.setBrush(QColor(Y));p.setPen(QPen(QColor(R),2));p.drawRoundedRect(box.adjusted(1,2,-1,-2),16,14)
            if f['id'] is None:self.txt(p,box.x()+5,box.y()+20,'none ×',15)
            else:self.icon(p,f,self.category,box.adjusted(4,4,-4,-4))
            hit=box.intersected(self.choice_rect);self.hits.append((hit,lambda f=f:self.choose(f['id']),f['name']))
        p.restore();self.max_library_scroll=max(0,math.ceil(len(choices)/cols)*cellh-self.choice_rect.height())
        self.line(p,[(x,b-130),(pad+l-16,b-130)],O,2)
        self.button(p,QRectF(x-5,b-124,161,29),'✎ freehand carver',lambda:self.tool('carve'),18,self.view.mode=='carve')
        self.button(p,QRectF(x+158,b-124,l-183,29),'undo cut',self.remove_cut,16)
        self.button(p,QRectF(x-3,b-92,145,27),('☑' if self.view.mirror else '☐')+' mirror cuts',self.toggle_mirror,17)
        self.txt(p,x,b-57,f'stabilize {round(self.view.stabilization*100)}%',15)
        self.slider(p,QRectF(x+109,b-60,l-146,22),self.view.stabilization,0,.95,self.set_stabilization)
        self.txt(p,x,b-28,'Draw a closed shape. Release to carve.',14)
        # Central toolbar and footer.
        self.button(p,QRectF(cx,t-2,76,30),'↶ undo',self.undo,18,enabled=bool(self.history));self.button(p,QRectF(cx+82,t-2,78,30),'↷ redo',self.redo,18,enabled=bool(self.future_history));self.button(p,QRectF(cx+166,t-2,95,30),'front view',self.view.front,18)
        self.button(p,QRectF(cx+cw-148,t-2,148,30),('☑' if self.d['lit'] else '☐')+' candlelight',self.toggle_glow,18)
        self.txt(p,cx+cw*.15,b-126,'draw a closed shape · release to carve' if self.view.mode=='carve' else 'drag to move the selected feature' if self.view.mode=='move' else 'drag to rotate · scroll to zoom',16)
        self.button(p,QRectF(cx+cw-154,b-132,154,30),'✥ move feature',lambda:self.tool('move'),16,self.view.mode=='move')
        self.txt(p,cx,b-75,'call me',19)
        actions=[('save to my patch',self.save),('export .glb',self.export_glb),('carving guide',self.guide),('save file',self.save_file),('open file',self.open_file)]
        total=cw/len(actions)
        for i,(label,fn)in enumerate(actions):self.button(p,QRectF(cx+i*total,b-28,total,27),label,fn,17)
        # Right part inspector / whole face collection.
        controlh=m-320;self.panel(p,rx,t,r,controlh,True)
        self.button(p,QRectF(rx+12,t+10,85,28),'this part',lambda:self.right_mode('part'),18)
        self.button(p,QRectF(rx+106,t+10,115,28),'whole faces',lambda:self.right_mode('presets'),18)
        tabx=rx+14 if self.right_tab=='part' else rx+110;self.line(p,[(tabx,t+38),(tabx+77,t+38)],R,3)
        if self.right_tab=='presets':
            self.txt(p,rx+14,t+50,'start with a whole face',22);self.txt(p,rx+14,t+79,'scary first · goofy faces below',15)
            self.presets_rect=QRectF(rx+12,t+108,r-24,controlh-120);p.save();p.setClipRect(self.presets_rect)
            for row,i in enumerate(PRESET_ORDER):
                rect=QRectF(rx+12+(row%3)*(r-24)/3,t+108+row//3*70-self.preset_scroll,(r-24)/3,67)
                if rect.intersects(self.presets_rect):self.draw_face(p,preset(i),rect);self.hits.append((rect.intersected(self.presets_rect),lambda i=i:self.apply_preset(i),preset(i)['name']))
            p.restore();self.max_preset_scroll=max(0,math.ceil(PRESET_COUNT/3)*70-self.presets_rect.height())
        else:
            self.txt(p,rx+14,t+51,NAMES.get(self.slot,dict(CATEGORIES).get(self.category)),29)
            self.button(p,QRectF(rx+14,t+90,92,27),'× remove',lambda:self.choose(None),16,enabled=self.category!='bodies')
            self.button(p,QRectF(rx+115,t+90,90,27),'↶ reset',self.reset_part,16,enabled=self.slot in self.d['parts'])
            if self.slot in self.d['parts']:
                part=self.d['parts'][self.slot];fields=[('x','left / right',-.95,.95),('y','down / up',-.95,.95),('sx','width',.025,1.05),('sy','height',.025,1.05),('rotation','rotation',-180,180)]
                if self.slot=='teeth':fields=[('x','spacing offset',-.4,.4),('y','vertical offset',-.4,.4),('sx','tooth width',.25,1.9),('sy','tooth length',.25,1.9)]
                for i,(key,label,lo,hi)in enumerate(fields):
                    y=t+134+i*51;self.txt(p,rx+14,y,label,17);self.txt(p,rx+r-65,y,f'{part[key]:.2f}' if key!='rotation' else f'{part[key]:.0f}°',15)
                    slider=QRectF(rx+18,y+23,r-36,20);self.slider(p,slider,part[key],lo,hi,lambda v,k=key:self.set_transform(k,v),bool(part['feature']))
            else:self.txt(p,rx+14,t+136,'Choose a style on the left.',17)
        bodyy=t+controlh+20;self.panel(p,rx,bodyy,r,215);self.txt(p,rx+14,bodyy+10,'the pumpkin itself',22);self.txt(p,rx+14,bodyy+44,'diameter',17);self.txt(p,rx+r-64,bodyy+44,f'{self.d["size"]:g} cm',15)
        self.slider(p,QRectF(rx+18,bodyy+66,r-36,20),self.d['size'],15,50,self.set_size)
        self.txt(p,rx+14,bodyy+94,'pick a peel',18)
        for i,color in enumerate([O,R,A,'#ff9200',Y]):
            rect=QRectF(rx+17+i*40,bodyy+119,28,27);p.setBrush(QColor(color));p.setPen(QPen(QColor(B),1));p.drawRoundedRect(rect,4,3)
            if self.d['color']==color:p.setBrush(Qt.NoBrush);p.setPen(QPen(QColor(R),2));p.drawRoundedRect(rect.adjusted(-3,-3,3,3),6,5)
            self.hits.append((rect,lambda c=color:self.set_color(c),'Peel '+color))
        self.txt(p,rx+14,bodyy+160,'a hollow 3D pumpkin.',16)
        self.txt(p,rx+14,bodyy+180,'a hand-drawn soul.',16)
        complete=QRectF(rx,b-65,r,65);p.setBrush(QColor(B));p.setPen(Qt.NoPen);p.drawRoundedRect(complete.translated(4,5),7,5);p.setBrush(QColor(R));p.setPen(QPen(QColor(B),2));p.drawRoundedRect(complete,5,6);p.setFont(font(31));p.setPen(QColor(C));p.drawText(complete,Qt.AlignCenter,'light it up!  ✦');self.hits.append((complete,self.complete,'Light it up'))
        self.txt(p,pad,h-33,self.message,15);self.txt(p,w-153,h-33,'all yours. all offline.',15)
        p.end()
    def slider(self,p,rect,value,lo,hi,fn,enabled=True):
        self.line(p,[(rect.left(),rect.center().y()),(rect.right(),rect.center().y())],B,3);x=rect.left()+max(0,min(1,(value-lo)/(hi-lo)))*rect.width();p.save();p.translate(x,rect.center().y());p.rotate(-5);p.fillRect(QRectF(-6,-10,12,20),QColor(R if enabled else A));p.restore()
        if enabled:self.hits.append((rect,('slider',fn,lo,hi,rect),'slider'))
    def mousePressEvent(self,e):
        if self.busy:return
        point=e.position()
        for rect,fn,label in reversed(self.hits):
            if not rect.contains(point):continue
            if isinstance(fn,tuple):self.remember();self.active_slider=fn;self.slide(point.x())
            else:fn()
            break
    def slide(self,x):
        kind,fn,lo,hi,rect=self.active_slider;fn(lo+max(0,min(1,(x-rect.left())/rect.width()))*(hi-lo))
    def mouseMoveEvent(self,e):
        if self.active_slider:self.slide(e.position().x())
        else:
            for rect,fn,label in reversed(self.hits):
                if rect.contains(e.position()):self.setCursor(Qt.PointingHandCursor);self.setToolTip(label);return
            self.unsetCursor();self.setToolTip('')
    def mouseReleaseEvent(self,e):self.active_slider=None
    def wheelEvent(self,e):
        if self.choice_rect.contains(e.position()):self.library_scroll=max(0,min(self.max_library_scroll,self.library_scroll-e.angleDelta().y()*.5));self.update()
        elif self.right_tab=='presets' and self.presets_rect.contains(e.position()):self.preset_scroll=max(0,min(self.max_preset_scroll,self.preset_scroll-e.angleDelta().y()*.5));self.update()
    def set_category(self,cat):self.category=cat;self.slot=SLOTS.get(cat,[cat])[0];self.library_scroll=0;self.update()
    def right_mode(self,tab):self.right_tab=tab;self.update()
    def target_menu(self):
        menu=QMenu(self);menu.setFont(font(18));menu.setStyleSheet('QMenu{background:#fffc78;color:#5d1e00;border:2px solid #5d1e00;}QMenu::item:selected{background:#ffbb0b;}')
        for slot in SLOTS.get(self.category,[]):menu.addAction(NAMES[slot],lambda s=slot:self.set_slot(s))
        menu.exec(self.mapToGlobal(self.rect().topLeft())+self.mapFromGlobal(__import__('PySide6.QtGui',fromlist=['QCursor']).QCursor.pos()).toPoint() if False else __import__('PySide6.QtGui',fromlist=['QCursor']).QCursor.pos())
    def set_slot(self,slot):self.slot=slot;self.update()
    def toggle_link(self):self.linked=not self.linked;self.update()
    def targets(self):return SLOTS[self.category] if self.linked and len(SLOTS.get(self.category,[]))==2 else [self.slot]
    def choose(self,feature):
        if feature is None and self.category=='bodies':return
        self.remember()
        if self.category in ('bodies','stems','lids'):self.d[{'bodies':'body','stems':'stem','lids':'lid'}[self.category]]=feature
        else:
            for key in self.targets():self.d['parts'][key]['feature']=feature;self.d['parts'][key]['visible']=True
        self.changed();self.status('Part changed. Every detail is yours to move or remove.' if feature else 'Part removed.')
    def set_transform(self,key,value):
        self.d['parts'][self.slot][key]=round(value,3)
        for other in self.targets():
            if other!=self.slot:self.d['parts'][other][key]=-value if key in ('x','rotation') else value
        self.changed()
    def set_size(self,value):self.d['size']=round(value);self.changed(False)
    def set_color(self,color):self.remember();self.d['color']=color;self.changed()
    def reset_part(self):
        if self.slot not in self.d['parts']:return
        self.remember()
        for key in self.targets():
            feature=self.d['parts'][key]['feature'];self.d['parts'][key]=copy.deepcopy(default_design()['parts'][key]);self.d['parts'][key]['feature']=feature
        self.changed()
    def tool(self,mode):
        if mode=='move' and self.slot not in PART_LIBRARY:return self.status('Choose a facial feature to move first.')
        self.view.set_mode('orbit' if self.view.mode==mode else mode);self.update()
    def move_feature(self,dx,dy,start):
        if start:self.remember();self.drag_start=copy.deepcopy(self.d['parts'][self.slot]);return
        if not self.drag_start:return
        for axis,delta in [('x',dx),('y',dy)]:self.d['parts'][self.slot][axis]=max(-.95,min(.95,self.drag_start[axis]+delta))
        for key in self.targets():
            if key!=self.slot:self.d['parts'][key]['x']=-self.d['parts'][self.slot]['x'];self.d['parts'][key]['y']=self.d['parts'][self.slot]['y']
        self.changed()
    def toggle_mirror(self):
        self.view.mirror=not self.view.mirror;self.view.update();self.update()
        self.status('Mirror on: both sides are carved together.' if self.view.mirror else 'Mirror off: carve freely.')
    def set_stabilization(self,value):self.view.stabilization=round(value,2);self.update()
    def add_cut(self,poly):
        area=abs(sum(poly[i-1][0]*p[1]-p[0]*poly[i-1][1] for i,p in enumerate(poly)))/2
        if area<.0002:return self.status('Draw a closed shape with a little area to make a cut.')
        from carving import mirrored_cuts
        additions=mirrored_cuts(poly,self.view.mirror)
        if len(self.d['cuts'])+len(additions)>80:return self.status('Undo a custom cut before adding another.')
        self.remember();self.d['cuts'].extend(additions);self.cut_groups.append(len(additions));self.changed();self.status('Mirrored carving added. Undo removes both sides.' if self.view.mirror else 'Stabilized carving added.')
    def remove_cut(self):
        if self.d['cuts']:
            self.remember()
            from carving import is_mirror_pair
            count=2 if len(self.d['cuts'])>=2 and is_mirror_pair(self.d['cuts'][-2],self.d['cuts'][-1]) else 1
            del self.d['cuts'][-count:];self.changed()
    def toggle_glow(self):self.remember();self.d['lit']=not self.d['lit'];self.changed(False)
    def complete(self):
        if self.busy:return
        self.remember();self.d['lit']=True;self.busy=True;self.name.setEnabled(False);self.view.set_mode('orbit');self.view.front();self.view.anim=time.monotonic();self.changed(False);self.status('Lifting the lid, lowering the candle, and lighting the night…')
    def finished(self):self.busy=False;self.name.setEnabled(True);self.status('Your pumpkin is ready for the night. Save it to your patch!')
    def apply_preset(self,i):
        self.remember();p=preset(i)
        for key in ('id','body','stem','lid','size','color','lit'):p[key]=self.d[key]
        p=validate(p)
        self.d=p;self.refresh();self.status('Face preset applied. Every part can still be changed or removed.')
    def new(self):self.remember();self.d=default_design();self.refresh();self.view.front();self.status('Fresh pumpkin. Your previous draft is one undo away.')
    def save(self):
        self.d['id']=self.d['id'] or uuid.uuid4().hex;path=DATA/(self.d['id']+'.json');temp=path.with_suffix('.tmp');temp.write_text(json.dumps(self.d,indent=2));temp.replace(path);self.changed(False);self.status('Saved to your pumpkin patch.')
    def save_folder(self):
        try:
            folder=Path((DATA/'save-folder.txt').read_text().strip())
            if folder.is_absolute() and folder!=Path(folder.anchor) and folder.is_dir() and os.access(folder,os.W_OK):return folder
        except OSError:pass
        documents=QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        folder=Path(documents) if documents else Path.home()/'Documents'
        return folder if folder.is_dir() and os.access(folder,os.W_OK) else Path.home()
    def pick_save(self,suffix,filter):
        folder=self.save_folder()
        name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',self.d['name']).strip(' .') or 'pumpkin'
        path=QFileDialog.getSaveFileName(self,'Save your pumpkin',str(folder/(name+suffix)),filter)[0]
        if not path:return ''
        target=Path(path).expanduser()
        if not target.is_absolute():target=folder/target
        if target.parent==Path(target.anchor) or not target.parent.is_dir() or not os.access(target.parent,os.W_OK):
            self.status('Choose a writable folder, such as Documents, and try saving again.');return ''
        return str(target)
    def saved_file(self,path,message):
        try:(DATA/'save-folder.txt').write_text(str(Path(path).resolve().parent))
        except OSError:pass
        self.status(message if reveal_file(path) else message+' Could not open the file manager.')
    def save_file(self):
        path=self.pick_save('.pumpkin','Pumpkin design (*.pumpkin)')
        if path:
            try:Path(path).write_text(json.dumps(self.d,indent=2));self.saved_file(path,'Editable pumpkin saved.')
            except OSError as e:QMessageBox.warning(self,'Could not save pumpkin',str(e))
    def open_file(self):
        path=QFileDialog.getOpenFileName(self,'Open pumpkin','','Pumpkin design (*.pumpkin *.json)')[0]
        if path:
            try:d=validate(json.loads(Path(path).read_text()));self.remember();self.d=d;self.d['id']=None;self.refresh()
            except (ValueError,OSError,KeyError,TypeError) as e:QMessageBox.warning(self,'Could not open pumpkin',str(e))
    def export_glb(self):
        path=self.pick_save('.glb','Binary glTF (*.glb)')
        if path:
            try:export(self.d,path);self.saved_file(path,'GLB exported: smooth openings, hollow walls, separate lid, units in metres.')
            except Exception as e:QMessageBox.warning(self,'Could not export',str(e))
    def guide(self):
        path=self.pick_save('-carving-guide.html','Printable guide (*.html)')
        if path:
            try:Path(path).write_text(write_guide(self.d));self.saved_file(path,'Guide saved. Open it in your browser and print at 100%.')
            except OSError as e:QMessageBox.warning(self,'Could not save guide',str(e))
    def show_overlay(self,panel):
        if self.overlay is not None:self.overlay.hide();self.overlay.deleteLater()
        self.overlay=panel(self);self.overlay.setGeometry(self.rect());self.view.hide();self.name.hide()
        self.overlay.show();self.overlay.raise_();self.overlay.setFocus()
    def close_overlay(self):
        if self.overlay is not None:self.overlay.hide();self.overlay.deleteLater();self.overlay=None
        self.view.show();self.name.show();self.view.update();self.setFocus()
    def gallery(self):
        from panels import GalleryPanel
        self.show_overlay(GalleryPanel)
    def help(self):
        from panels import InfoPanel
        self.show_overlay(InfoPanel)
    def closeEvent(self,e):
        self.changed(False);self.delay.stop();self.poll.stop();self.pool.shutdown(wait=False,cancel_futures=True);shutdown_previews();e.accept()

def run():
    fmt=QSurfaceFormat();fmt.setVersion(3,3);fmt.setProfile(QSurfaceFormat.CoreProfile);fmt.setDepthBufferSize(24);fmt.setSamples(4);QSurfaceFormat.setDefaultFormat(fmt)
    app=QApplication(sys.argv);app.setApplicationName('Pumpkin Patch');app.setWindowIcon(QIcon(str(ROOT/'assets/icons/pumpkin-patch.png')));QFontDatabase.addApplicationFont(str(ROOT/'assets/fonts/PatrickHand-Regular.ttf'));app.setFont(font(19))
    window=Patch();window.show()
    sys.exit(app.exec())
if __name__=='__main__':run()
