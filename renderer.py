"""Python-owned OpenGL doodle renderer. Smooth carved meshes, no voxel geometry."""
import ctypes,math,time
import numpy as np
from PySide6.QtCore import Qt,QTimer,QPointF,Signal
from PySide6.QtGui import QColor,QPainter,QPen,QFont
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
from library import LIBRARY
from mesh import surface
from carving import face_hit

VERT='''#version 150
in vec3 position;in vec3 normal;uniform mat4 projectionMatrix;uniform mat4 modelViewMatrix;uniform mat3 normalMatrix;uniform float centerY;uniform float outline;uniform float time;uniform float special;uniform float flameBase;out float across;out vec3 n;out vec3 p;out float interior;
void main(){interior=dot(normal,position-vec3(0.,centerY,0.))<0.?1.:0.;n=normalize(normalMatrix*normal);p=position;vec3 v=position+normal*outline*(.008+.002*sin(position.y*23.+position.x*18.));if(special>2.5){float h=clamp((position.y-flameBase)/.26,0.,1.);v.x+=sin(time*5.7)*.014*h*h;v.z+=sin(time*7.3)*.006*h*h;}across=(modelViewMatrix*vec4(position,0.)).x;gl_Position=projectionMatrix*modelViewMatrix*vec4(v,1.);}
'''
FRAG='''#version 150
in float across;in vec3 n;in vec3 p;in float interior;uniform vec3 peel;uniform float time;uniform float lit;uniform float special;uniform float outline;uniform float flameBase;out vec4 color;
void main(){vec3 brown=vec3(.365,.118,0.);vec3 amber=vec3(1.,.733,.043);vec3 orange=vec3(1.,.51,0.);vec3 pale=vec3(1.,.988,.471);vec3 red=vec3(1.,.322,0.);vec3 c=peel;
if(outline>.5)c=brown;
else if(special>2.5){float h=p.y-flameBase;float core=.022*sqrt(max(0.,1.-pow((h-.085)/.095,2.)));c=abs(across)<core&&h<.18?pale:amber;}
else if(special>1.5)c=dot(normalize(n),normalize(vec3(-.6,.5,1.)))<.05?amber:pale;
else if(special>.5)c=brown;
else{float shade=dot(normalize(n),normalize(vec3(-.7,.8,1.)));if(interior>.5){float flicker=sin(time*7.)*.12+sin(time*13.)*.06;c=lit>.5?(p.y<.8+flicker?amber:orange):brown;}else if(peel.g>.62){if(shade<.12)c=vec3(185./255.,77./255.,0.);else if(shade>.85)c=pale;else if(shade<.4)c=orange;else c=peel;}else if(peel.g<.4){if(shade<.18)c=vec3(185./255.,77./255.,0.);else if(shade>.94)c=amber;else if(shade>.76)c=orange;else c=peel;}else{if(shade<.12)c=vec3(185./255.,77./255.,0.);else if(shade<.4)c=red;else if(shade>.96)c=pale;else if(shade>.8)c=amber;else c=peel;}}
color=vec4(c,1.);}
'''

def perspective(fov,aspect,near,far):
    f=1/math.tan(math.radians(fov)/2)
    return np.array([[f/aspect,0,0,0],[0,f,0,0],[0,0,(far+near)/(near-far),2*far*near/(near-far)],[0,0,-1,0]],dtype=np.float32)
def orbit_drag(yaw,pitch,dx,dy,height):
    sensitivity=math.tau/max(300,height)
    # Move the visible surface with the hand, matching the former orbit controls.
    return yaw-dx*sensitivity,max(-1.42,min(1.42,pitch+dy*sensitivity))

def lookat(eye,target):
    f=target-eye;f/=np.linalg.norm(f);s=np.cross(f,[0,1,0]);s/=np.linalg.norm(s);u=np.cross(s,f)
    m=np.eye(4,dtype=np.float32);m[0,:3]=s;m[1,:3]=u;m[2,:3]=-f;m[:3,3]=-m[:3,:3]@eye
    return m

class PumpkinView(QOpenGLWidget):
    carved=Signal(list)
    moved=Signal(float,float,bool)
    status=Signal(str)
    animationDone=Signal()
    def __init__(self,parent=None):
        super().__init__(parent);self.design=None;self.pending=None;self.objects=[];self.program=None;self.yaw=0;self.pitch=0;self.distance=5.9;self.mode='orbit';self.stabilization=.70;self.mirror=False;self.drag=None;self.stroke=[];self.anim=None;self.error=None
        self.setMouseTracking(True);self.clock=QTimer(self);self.clock.timeout.connect(self.animate_tick);self.clock.start(33)
    def animate_tick(self):
        if self.isVisible() and (self.anim or (self.design and self.design['lit'])):self.update()
    def initializeGL(self):
        try:
            self.program=compileProgram(compileShader(VERT,GL_VERTEX_SHADER),compileShader(FRAG,GL_FRAGMENT_SHADER),validate=False)
            self.locations={n:glGetUniformLocation(self.program,n) for n in ['projectionMatrix','modelViewMatrix','normalMatrix','centerY','outline','peel','time','lit','special','flameBase']}
            glEnable(GL_DEPTH_TEST);glEnable(GL_CULL_FACE)
        except Exception as e:self.error=str(e);self.status.emit('The graphics driver could not start: '+str(e))
    def set_parts(self,parts,design):self.pending=parts;self.design=design;self.update()
    def upload(self):
        for o in self.objects:
            glDeleteBuffers(2,[o['vbo'],o['ebo']]);glDeleteVertexArrays(1,[o['vao']])
        self.objects=[]
        for p in self.pending:
            verts=np.asarray(p.vertices,dtype=np.float32);normals=np.asarray(p.normals,dtype=np.float32);data=np.concatenate([verts,normals],axis=1).astype(np.float32);indices=np.asarray(p.faces,dtype=np.uint32).flatten()
            vao=glGenVertexArrays(1);glBindVertexArray(vao);vbo=glGenBuffers(1);ebo=glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER,vbo);glBufferData(GL_ARRAY_BUFFER,data.nbytes,data,GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,ebo);glBufferData(GL_ELEMENT_ARRAY_BUFFER,indices.nbytes,indices,GL_STATIC_DRAW)
            for key,offset in [('position',0),('normal',12)]:
                loc=glGetAttribLocation(self.program,key);glEnableVertexAttribArray(loc);glVertexAttribPointer(loc,3,GL_FLOAT,False,24,ctypes.c_void_p(offset))
            self.objects.append(dict(vao=vao,vbo=vbo,ebo=ebo,count=len(indices),name=p.name,color=p.color))
        glBindVertexArray(0);self.pending=None
    def body(self):return next(b for b in LIBRARY['bodies'] if b['id']==self.design['body']) if self.design else LIBRARY['bodies'][0]
    def matrices(self):
        sy=self.body()['sy'];eye=np.array([self.distance*math.sin(self.yaw)*math.cos(self.pitch),sy+self.distance*math.sin(self.pitch),self.distance*math.cos(self.yaw)*math.cos(self.pitch)],dtype=np.float32)
        return perspective(34,max(.1,self.width()/max(1,self.height())),.05,30),lookat(eye,np.array([0,sy,0],dtype=np.float32))
    def paintGL(self):
        glClearColor(1,213/255,36/255,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        if self.program and self.design:
            if self.pending is not None:self.upload()
            glEnable(GL_DEPTH_TEST);glEnable(GL_CULL_FACE);glDepthFunc(GL_LESS);glUseProgram(self.program)
            proj,view=self.matrices();loc=self.locations
            glUniformMatrix4fv(loc['projectionMatrix'],1,GL_TRUE,proj);glUniform1f(loc['centerY'],self.body()['sy']);glUniform1f(loc['lit'],float(self.design['lit']));glUniform1f(loc['time'],time.monotonic())
            glUniform1f(loc['flameBase'],surface(0,math.pi,self.body(),inner=True)[1]+.018+.498)
            elapsed=time.monotonic()-self.anim if self.anim else None
            if elapsed is not None and elapsed>3.8:self.anim=None;self.animationDone.emit();elapsed=None
            for obj in self.objects:
                name=obj['name'];offset=0
                if name in ('candle','wick','flame'):
                    if not self.design['lit'] or (elapsed is not None and elapsed<1):continue
                    if elapsed is not None:offset=max(0,(2.5-elapsed)/1.5*3)
                if name in ('lid','stem') and elapsed is not None:offset=elapsed*.9 if elapsed<1 else .9 if elapsed<2.5 else max(0,.9*(1-(elapsed-2.5)/1.1))
                move=np.eye(4,dtype=np.float32);move[1,3]=offset;mv=view@move
                glUniformMatrix4fv(loc['modelViewMatrix'],1,GL_TRUE,mv);glUniformMatrix3fv(loc['normalMatrix'],1,GL_TRUE,np.linalg.inv(mv[:3,:3]).T)
                glUniform3f(loc['peel'],*obj['color']);glUniform1f(loc['special'],{'stem':1,'wick':1,'candle':2,'flame':3}.get(name,0));glBindVertexArray(obj['vao'])
                glCullFace(GL_FRONT);glUniform1f(loc['outline'],1);glDrawElements(GL_TRIANGLES,obj['count'],GL_UNSIGNED_INT,None)
                glCullFace(GL_BACK);glUniform1f(loc['outline'],0);glDrawElements(GL_TRIANGLES,obj['count'],GL_UNSIGNED_INT,None)
            glBindVertexArray(0);glUseProgram(0)
        glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE)
        painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing);painter.setPen(QPen(QColor('#ffbb0b'),2));painter.drawEllipse(8,35,self.width()-16,self.height()-80)
        f=QFont('Patrick Hand');f.setPixelSize(22);painter.setFont(f);painter.setPen(QColor('#5d1e00'));painter.drawText(self.width()-125,55,'Pumpkin!');painter.drawText(self.width()-108,108,'↙')
        f.setPixelSize(27);painter.setFont(f);painter.setPen(QColor('#ff5200'));painter.drawText(7,int(self.height()*.30),'✳');painter.drawText(self.width()-20,int(self.height()*.74),'+')
        if self.mode=='carve' and self.mirror:
            painter.setPen(QPen(QColor('#ff8200'),1,Qt.DashLine));painter.drawLine(self.width()//2,35,self.width()//2,self.height()-25)
        if self.stroke:
            painter.setPen(QPen(QColor('#5d1e00'),3));painter.drawPolyline([QPointF(p[2],p[3]) for p in self.stroke])
            if self.mirror:
                painter.setPen(QPen(QColor('#ff5200'),2));painter.drawPolyline([QPointF(self.width()-p[2],p[3]) for p in self.stroke])
        if self.error:
            painter.setPen(QColor('#5d1e00'));painter.drawText(20,self.height()//2,'Graphics error — see status below.')
        painter.end()
    def front(self):self.drag=None;self.yaw=0;self.pitch=0;self.distance=max(5.4,self.body()['sy']*5.1);self.update()
    def set_mode(self,mode):self.mode=mode;self.stroke=[];self.drag=None;self.setCursor(Qt.OpenHandCursor if mode=='orbit' else Qt.CrossCursor);self.front() if mode!='orbit' else self.update()
    def face_point(self,x,y):
        proj,view=self.matrices();inv=np.linalg.inv(proj@view);p1=inv@np.array([x/self.width()*2-1,1-y/self.height()*2,-1,1]);p2=inv@np.array([x/self.width()*2-1,1-y/self.height()*2,1,1]);p1=p1[:3]/p1[3];p2=p2[:3]/p2[3]
        hit=face_hit(p1,p2-p1,self.body())
        return None if hit is None else hit+[x,y]
    def mousePressEvent(self,e):
        if self.anim or e.button()!=Qt.LeftButton:return
        x,y=e.position().x(),e.position().y();point=self.face_point(x,y)
        self.drag=(x,y,point)
        if self.mode=='carve' and point:self.stroke=[point]
        if self.mode=='move' and point:self.moved.emit(0,0,True)
    def mouseMoveEvent(self,e):
        if not (e.buttons() & Qt.LeftButton):self.drag=None;return
        if not self.drag:return
        x,y=e.position().x(),e.position().y();oldx,oldy,oldp=self.drag
        if self.mode=='orbit':self.yaw,self.pitch=orbit_drag(self.yaw,self.pitch,x-oldx,y-oldy,self.height());self.drag=(x,y,oldp)
        else:
            point=self.face_point(x,y)
            if point and self.mode=='carve' and len(self.stroke)<1000:
                if not self.stroke:self.stroke.append(point)
                else:
                    last=self.stroke[-1];distance=math.hypot(x-last[2],y-last[3])
                    # Slow movement is smoothed more strongly; fast strokes remain responsive.
                    alpha=max(.08,1-self.stabilization*.90)
                    alpha=min(1,alpha+min(distance/90,.25))
                    sx=last[2]+(x-last[2])*alpha;sy=last[3]+(y-last[3])*alpha
                    filtered=self.face_point(sx,sy)
                    if filtered and math.hypot(sx-last[2],sy-last[3])>.75:self.stroke.append(filtered)
            if point and self.mode=='move' and oldp:self.moved.emit(point[0]-oldp[0],point[1]-oldp[1],False)
        self.update()
    def mouseReleaseEvent(self,e):
        if self.mode=='carve' and self.stroke:
            point=self.face_point(e.position().x(),e.position().y())
            if point and math.hypot(point[2]-self.stroke[-1][2],point[3]-self.stroke[-1][3])>.5:self.stroke.append(point)
        if self.mode=='carve' and len(self.stroke)>=3:
            from carving import smooth_stroke
            self.carved.emit(smooth_stroke([p[:2] for p in self.stroke],self.stabilization))
        self.drag=None;self.stroke=[];self.update()
    def wheelEvent(self,e):
        if self.drag and self.mode!='orbit':return
        self.distance=max(3.4,min(9,self.distance-e.angleDelta().y()*.002));self.update()
