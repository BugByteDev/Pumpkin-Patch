"""Painted in-app pages. No dialogs, OS window chrome or native scrollbars."""
import copy,json,math
from PySide6.QtCore import Qt,QRectF,QPointF,QUrl
from PySide6.QtGui import QPainter,QColor,QPen,QFontMetricsF,QDesktopServices
from PySide6.QtWidgets import QWidget
from native import CanvasHelpers,font,Y,C,O,A,R,B
from storage import DATA,validate

class Panel(QWidget,CanvasHelpers):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.scroll=0;self.max_scroll=0;self.hits=[]
        self.setFocusPolicy(Qt.StrongFocus);self.setMouseTracking(True)
    def shell(self,p,title,subtitle):
        p.setRenderHint(QPainter.Antialiasing);p.fillRect(self.rect(),QColor(Y))
        w=min(940,self.width()-64);h=self.height()-72;x=(self.width()-w)/2;y=32
        self.panel(p,x,y,w,h,True);self.txt(p,x+24,y+22,title,36)
        self.txt(p,x+25,y+70,subtitle,18)
        close=QRectF(x+w-117,y+20,91,39);p.setPen(QPen(QColor(B),2));p.setBrush(QColor(Y));p.drawRoundedRect(close,5,5)
        self.txt(p,close.x()+14,close.y()+7,'close ×',21);self.hits=[(close,'close',None)]
        self.content=QRectF(x+22,y+108,w-54,h-132)
        return x,y,w,h
    def scrollbar(self,p):
        if self.max_scroll<=0:return
        rect=QRectF(self.content.right()+10,self.content.top(),7,self.content.height())
        p.fillRect(rect,QColor(A));size=max(28,rect.height()**2/(rect.height()+self.max_scroll))
        p.fillRect(QRectF(rect.x(),rect.y()+(rect.height()-size)*self.scroll/self.max_scroll,7,size),QColor(B))
    def mousePressEvent(self,e):
        for rect,action,index in reversed(self.hits):
            if rect.contains(e.position()):
                if action=='close':self.owner.close_overlay()
                else:self.action(action,index)
                break
    def action(self,action,index):pass
    def wheelEvent(self,e):self.scroll=max(0,min(self.max_scroll,self.scroll-e.angleDelta().y()*.5));self.update()
    def keyPressEvent(self,e):
        if e.key()==Qt.Key_Escape:self.owner.close_overlay()
        elif e.key() in (Qt.Key_Down,Qt.Key_PageDown):self.scroll=min(self.max_scroll,self.scroll+100);self.update()
        elif e.key() in (Qt.Key_Up,Qt.Key_PageUp):self.scroll=max(0,self.scroll-100);self.update()

class InfoPanel(Panel):
    REPOSITORY='https://github.com/BugByteDev/Pumpkin-Patch'
    def action(self,action,index):
        if action=='repository':QDesktopServices.openUrl(QUrl(self.REPOSITORY))
    paragraphs=[
      ('MAKE IT YOURS','Choose a body, stem and lid, then add eyes, brows, a nose, a mouth, teeth or details. Every piece has a None / remove option. New pumpkins start with a blank face.'),
      ('MOVE EACH PIECE','Use the sliders for position, width, height and rotation. Link a pair to edit both sides together, or choose one side to make an uneven face.'),
      ('WHOLE FACES','The whole faces tab has scary and goofy starting points. After choosing one, every piece can still be changed or removed.'),
      ('CARVE YOUR OWN','Choose the freehand carver, draw a closed shape and release to cut it out. Stabilization smooths your stroke. Mirror cuts reflects it onto the other side. Undo cut removes the last carving.'),
      ('LOOK AROUND','Drag the pumpkin to rotate it. Scroll to zoom. Front view resets the camera. Move feature lets you drag the selected face piece.'),
      ('CANDLELIGHT','Light it up lifts the lid, lowers a candle and lights the pumpkin. The candlelight toggle switches the light on or off while keeping the doodle style.'),
      ('SAVE AND SHARE','Save to my patch keeps a pumpkin in your gallery. Save file creates an editable .pumpkin file. Export .glb makes a 3D model. Carving guide creates printable instructions. Saved files are shown in Finder.'),
      ('QUICK KEYS','Command Z: undo. Shift Command Z: redo. Escape: close this page or leave a drawing tool.'),
      ('ALL OFFLINE','Blender is not needed to use the app. Preset previews are bundled. Your edited pumpkin meshes and previews are cached locally, so reopening them reuses the saved renders.')]
    def paintEvent(self,e):
        p=QPainter(self);self.shell(p,'welcome to the patch','Everything you need to make your pumpkin.');p.save();p.setClipRect(self.content)
        y=self.content.top()-self.scroll
        button=QRectF(self.content.left()+4,y,270,42)
        p.setPen(QPen(QColor(B),2));p.setBrush(QColor(Y));p.drawRoundedRect(button,5,5)
        self.txt(p,button.x()+12,button.y()+8,'open GitHub repository ↗',21)
        self.hits.append((button.intersected(self.content),'repository',None))
        y+=66;metrics=QFontMetricsF(font(21))
        for title,text in self.paragraphs:
            self.txt(p,self.content.left()+4,y,title,23,R);y+=35
            bounds=metrics.boundingRect(QRectF(0,0,self.content.width()-18,4000),Qt.TextWordWrap,text)
            p.setFont(font(21));p.setPen(QColor(B));p.drawText(QRectF(self.content.left()+4,y,self.content.width()-18,bounds.height()+6),Qt.TextWordWrap,text);y+=bounds.height()+34
        self.max_scroll=max(0,y+self.scroll-self.content.bottom());p.restore();self.scrollbar(p);p.end()

class GalleryPanel(Panel):
    def __init__(self,owner):
        super().__init__(owner);self.items=[];self.confirm=None;self.error=''
        for file in DATA.glob('*.json'):
            try:self.items.append((file,validate(json.loads(file.read_text()))))
            except (OSError,ValueError,KeyError,TypeError):pass
    def paintEvent(self,e):
        p=QPainter(self);self.shell(p,'your pumpkin patch',self.error or 'Saved here, ready for another tweak.');p.save();p.setClipRect(self.content)
        cols=max(1,int(self.content.width()//267));cellw=self.content.width()/cols
        if not self.items:self.txt(p,self.content.x()+12,self.content.y()+30,'No pumpkins yet. Save your first one!',27)
        for i,(path,d) in enumerate(self.items):
            x=self.content.x()+i%cols*cellw+5;y=self.content.y()+i//cols*233-self.scroll
            if y+215<self.content.top() or y>self.content.bottom():continue
            w=cellw-18;self.panel(p,x,y,w,210);self.draw_face(p,d,QRectF(x+(w-150)/2,y+4,150,131));self.txt(p,x+12,y+138,d['name'][:25] or 'Unnamed pumpkin',21)
            if self.confirm==i:
                self.txt(p,x+12,y+171,'remove?',17,R)
                for label,action,xx in [('yes','confirm',x+96),('cancel','cancel',x+145)]:
                    self.txt(p,xx,y+174,label,18);self.hits.append((QRectF(xx,y+170,66,33).intersected(self.content),action,i))
            else:
                for label,action,xx in [('open','open',x+20),('delete','delete',x+w-83)]:
                    self.txt(p,xx,y+177,label,20,R if action=='delete' else B);self.hits.append((QRectF(xx-6,y+169,81,36).intersected(self.content),action,i))
        self.max_scroll=max(0,math.ceil(len(self.items)/cols)*233-self.content.height());p.restore();self.scrollbar(p);p.end()
    def action(self,action,index):
        if action=='cancel':self.confirm=None
        elif action=='delete':self.confirm=index
        elif action=='open':
            self.owner.remember();self.owner.d=copy.deepcopy(self.items[index][1]);self.owner.refresh();self.owner.close_overlay();return
        elif action=='confirm' and self.confirm==index:
            path,d=self.items[index]
            try:path.unlink()
            except OSError:self.error='Could not remove that pumpkin. Try again.'
            else:
                self.items.pop(index)
                if self.owner.d['id']==d['id']:self.owner.d['id']=None;self.owner.changed(False)
            self.confirm=None
        self.update()
