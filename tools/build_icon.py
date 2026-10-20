"""Package the Blender-rendered app icon, retaining the vector source as a fallback."""
import os,re,struct,sys
import xml.etree.ElementTree as ET
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QPainter,QPainterPath,QColor,QPen
from PySide6.QtCore import Qt,QBuffer,QIODevice,QRectF
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/icons'
app=QApplication.instance() or QApplication([])
rendered=QImage(str(OUT/'pumpkin-render.png'))
svg=ET.parse(OUT/'pumpkin-patch.svg').getroot()
def draw(painter,node,inherited=None):
    style=dict(inherited or {});style.update(node.attrib)
    tag=node.tag.split('}')[-1]
    if tag in ('rect','path'):
        path=QPainterPath()
        if tag=='rect':
            from PySide6.QtCore import QRectF
            path.addRoundedRect(QRectF(*[float(style[x]) for x in ('x','y','width','height')]),float(style.get('rx',0)),float(style.get('rx',0)))
        else:
            tokens=re.findall(r'[MLCQZ]|[-+]?(?:[0-9]*[.])?[0-9]+',style['d']);i=0
            while i<len(tokens):
                cmd=tokens[i];i+=1
                count={'M':2,'L':2,'C':6,'Q':4,'Z':0}[cmd]
                args=list(map(float,tokens[i:i+count]));i+=count
                {'M':path.moveTo,'L':path.lineTo,'C':path.cubicTo,'Q':path.quadTo,'Z':path.closeSubpath}[cmd](*args)
        fill=style.get('fill','#5d1e00');stroke=style.get('stroke','none')
        painter.setBrush(Qt.NoBrush if fill=='none' else QColor(fill))
        if stroke=='none':painter.setPen(Qt.NoPen)
        else:
            pen=QPen(QColor(stroke),float(style.get('stroke-width',1)));pen.setJoinStyle(Qt.RoundJoin);pen.setCapStyle(Qt.RoundCap);painter.setPen(pen)
        painter.drawPath(path)
    for child in node:draw(painter,child,style)
def png(size):
    image=QImage(size,size,QImage.Format_ARGB32);image.fill(Qt.transparent)
    painter=QPainter(image);painter.setRenderHint(QPainter.Antialiasing);painter.scale(size/1024,size/1024)
    if rendered.isNull():draw(painter,svg)
    else:
        painter.setRenderHint(QPainter.SmoothPixmapTransform);painter.setPen(Qt.NoPen);painter.setBrush(QColor('#ffd524'));painter.drawRoundedRect(QRectF(56,56,912,912),210,210)
        painter.drawImage(QRectF(0,0,1024,1024),rendered)
    painter.end()
    buffer=QBuffer();buffer.open(QIODevice.WriteOnly);assert image.save(buffer,'PNG')
    return bytes(buffer.data())
# PNG-backed ICNS chunks are supported by macOS 10.7 and later.
chunks=[]
for tag,size in [(b'icp4',16),(b'icp5',32),(b'icp6',64),(b'ic07',128),(b'ic08',256),(b'ic09',512),(b'ic10',1024)]:
    data=png(size);chunks.append(tag+struct.pack('>I',len(data)+8)+data)
payload=b''.join(chunks);(OUT/'pumpkin-patch.icns').write_bytes(b'icns'+struct.pack('>I',len(payload)+8)+payload)
(OUT/'pumpkin-patch-3d.icns').write_bytes((OUT/'pumpkin-patch.icns').read_bytes())
images=[(size,png(size)) for size in (16,24,32,48,64,128,256)]
header=struct.pack('<HHH',0,1,len(images));offset=6+16*len(images);entries=[]
for size,data in images:
    entries.append(struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(data),offset));offset+=len(data)
(OUT/'pumpkin-patch.ico').write_bytes(header+b''.join(entries)+b''.join(data for _,data in images))
(OUT/'pumpkin-patch.png').write_bytes(png(1024))
print('Created PNG, ICNS and ICO app icons from the Blender render')
