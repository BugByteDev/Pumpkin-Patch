"""Original, editable vector feature library. No generated raster artwork."""
import math

def oval(rx=1,ry=1,n=28,cx=0,cy=0):
    return [[cx+rx*math.cos(i*math.tau/n),cy+ry*math.sin(i*math.tau/n)] for i in range(n)]
def item(id,name,poly,**kw):return dict(id=id,name=name,polygons=poly,**kw)
def p(id,name,points):return item(id,name,[points])
EYES=[p('triangle','Classic triangle',[[-1,-.8],[1,-.8],[0,1]]),item('round','Round',[oval()]),p('diamond','Diamond',[[0,1],[1,0],[0,-1],[-1,0]]),p('sleepy','Sleepy',[[-1,.2],[1,.2],[.7,-.4],[-.8,-.4]]),p('angry','Angry wedge',[[-1,.8],[1,-.1],[.6,-.9],[-.7,-.7]]),p('happy','Happy arch',[[-1,-.5],[-.5,.5],[0,.8],[.5,.5],[1,-.5],[.5,-.1],[0,.25],[-.5,-.1]]),p('droop','Droopy',[[-1,.1],[-.5,.7],[.5,.7],[1,.1],[.5,-.8],[-.5,-.6]]),p('upside','Upside triangle',[[-1,.8],[1,.8],[0,-1]]),p('wink','Wink',[[-1,.1],[1,.1],[1,-.15],[-1,-.15]]),item('tall','Tall oval',[oval(.63,1)]),item('tiny','Tiny dot',[oval(.40,.40)]),p('squint','Squint',[[-1,.3],[1,-.05],[.95,-.4],[-1,-.05]]),p('star','Star',[[math.cos(i*math.pi/5-math.pi/2)*(1 if i%2==0 else .44),math.sin(i*math.pi/5-math.pi/2)*(1 if i%2==0 else .44)] for i in range(10)]),p('heart','Heart',[[-1,.4],[-.8,.9],[-.3,1],[0,.6],[.3,1],[.8,.9],[1,.4],[.7,-.2],[0,-1],[-.7,-.2]]),p('cross','Cross',[[-1,.6],[-.6,1],[0,.4],[.6,1],[1,.6],[.4,0],[1,-.6],[.6,-1],[0,-.4],[-.6,-1],[-1,-.6],[-.4,0]]),p('crescent','Crescent',[[-.8,1],[-1,.4],[-.8,-.5],[0,-1],[.8,-.5],[1,.4],[.8,1],[.55,.2],[0,-.25],[-.55,.2]]),p('bean','Bean',[[-.8,.8],[-1,.1],[-.5,-.7],[.4,-1],[1,-.5],[.8,.3],[.2,.1],[-.2,.5]]),p('teardrop','Teardrop',[[0,1],[-.8,-.1],[-.7,-.7],[0,-1],[.7,-.7],[.8,-.1]]),p('side','Side glance',[[-1,.4],[.5,.8],[1,.3],[.6,-.6],[-.7,-.5]]),p('spark','Spark',[[0,1],[.25,.2],[1,0],[.25,-.2],[0,-1],[-.25,-.2],[-1,0],[-.25,.2]]),p('square','Soft square',[[-.7,1],[.7,1],[1,.7],[1,-.7],[.7,-1],[-.7,-1],[-1,-.7],[-1,.7]]),p('roundtop','Round top',[[-1,-.6],[-1,.2],[-.6,.9],[0,1],[.6,.9],[1,.2],[1,-.6]]),p('lash','Lash wedge',[[-1,1],[-.4,.5],[1,.3],[.8,-.6],[-.7,-.8]]),p('soft','Soft arch',[[-1,-.1],[-.6,.7],[0,1],[.6,.7],[1,-.1],[.4,.2],[0,.4],[-.4,.2]])]
EYES.extend([
    p('glare','Deep glare',[[-1,.65],[.8,.05],[1,-.40],[-.65,-.6]]),
    p('slash','Slashed eye',[[-1,.8],[1,-.25],[.8,-.65],[-.85,.35]]),
    p('skull','Skull socket',[[-.9,.6],[-.35,1],[.55,.8],[1,.25],[.65,-.8],[-.55,-1],[-1,-.3]]),
    p('hook','Hooked eye',[[-1,.75],[.9,-.1],[.8,-.8],[.15,-.35],[-.65,-.55]]),
    p('hollow','Hollow socket',[[-.7,1],[.45,.85],[1,.2],[.7,-.9],[-.4,-1],[-1,-.15]]),
    p('needle','Needle glare',[[-1,.35],[1,-.05],[.55,-.35],[-.85,-.05]])
])
EYES.extend([
 p('demon','Demon wedge',[[-1,.9],[.9,-.15],[.7,-.8],[-.8,-.45]]),
 p('sunken','Sunken socket',[[-1,.3],[-.6,1],[.5,.65],[1,-.2],[.4,-.85],[-.65,-.9]]),
 p('knife','Knife slit',[[-1,.7],[1,-.2],[.85,-.4],[-.9,.4]]),
 p('bat','Bat wing eye',[[-1,.85],[-.25,.2],[.9,.05],[.5,-.75],[-.15,-.35],[-.75,-.65]]),
 p('cracked','Cracked socket',[[-.8,1],[.2,.7],[.8,1],[.6,.1],[1,-.3],[.3,-1],[-.65,-.7],[-1,.1]]),
 p('sickle','Sickle eye',[[-1,.9],[-.2,.45],[.9,.5],[.45,-.55],[-.3,-.85],[-.05,-.1],[-.7,-.2]])
])
for feature in EYES[24:]:feature['scary']=True
BASE_MOUTHS=[
('grin','Grin',[[-1,.65],[-.65,.2],[0,0],[.65,.2],[1,.65],[.75,-.45],[.35,-.85],[0,-1],[-.4,-.85],[-.8,-.4]]),
('big','Big open',[[-.7,1],[.7,1],[1,.7],[1,-.6],[.7,-1],[-.7,-1],[-1,-.6],[-1,.7]]),
('gasp','Gasp',oval(.7,1)),
('laugh','Laugh',[[-1,.65],[-.4,.85],[.4,.85],[1,.65],[.8,-.5],[.4,-.95],[-.4,-.95],[-.8,-.5]]),
('smirk','Smirk',[[-1,.1],[-.4,-.1],[.3,.1],[1,.8],[.8,-.3],[.2,-.8],[-.5,-.6]]),
('frown','Frown',[[-1,-.4],[-.65,.45],[0,.95],[.65,.45],[1,-.4],[.4,.1],[0,.3],[-.4,.1]]),
('zig','Zigzag',[[-1,.2],[-.65,.7],[-.3,.2],[0,.7],[.35,.2],[.7,.7],[1,.2],[.85,-.5],[.5,-.1],[.15,-.6],[-.2,-.1],[-.55,-.6],[-.9,-.2]]),
('smile','Soft smile',[[-1,.3],[-.4,-.1],[.4,-.1],[1,.3],[.65,-.65],[0,-.9],[-.65,-.65]]),
('square','Square shout',[[-1,1],[1,1],[1,-1],[-1,-1]]),
('wide','Wide shout',[[-.8,.9],[.8,.9],[1,.45],[1,-.45],[.8,-.9],[-.8,-.9],[-1,-.45],[-1,.45]]),
('wonky','Wonky grin',[[-1,.55],[-.6,.1],[0,.2],[.6,.65],[1,.9],[.8,-.3],[.3,-.9],[-.3,-.65],[-.8,-.5]]),
('tiny','Tiny gasp',oval(.45,.7)),
('cat','Cat smile',[[-1,.35],[-.6,.05],[-.25,.15],[0,.55],[.25,.15],[.6,.05],[1,.35],[.7,-.55],[.3,-.7],[0,-.4],[-.3,-.7],[-.7,-.55]]),
('silly','Silly pout',[[-.8,.45],[-.3,.75],[.3,.75],[.8,.45],[1,0],[.65,-.45],[0,-.85],[-.65,-.45],[-1,0]]),
('cheer','Cheer',[[-1,.45],[0,.9],[1,.45],[.65,-.5],[0,-1],[-.65,-.5]]),
('flat','Deadpan',[[-1,.15],[1,.15],[1,-.15],[-1,-.15]])]
BASE_MOUTHS.extend([
('saw','Sawtooth grin',[[-1,.75],[-.65,.35],[-.4,.6],[-.12,.25],[.14,.55],[.4,.25],[.68,.5],[1,.8],[.85,-.4],[.6,-.15],[.35,-.65],[.08,-.35],[-.2,-.75],[-.48,-.35],[-.78,-.5]]),
('snarl','Snarl',[[-1,.45],[-.55,.85],[.12,.25],[.65,.8],[1,.5],[.72,-.65],[.25,-.9],[-.25,-.5],[-.75,-.8]]),
('skullgrin','Skull grin',[[-1,.55],[-.6,.8],[.6,.8],[1,.55],[.9,-.55],[.45,-.85],[-.45,-.85],[-.9,-.55]]),
('howl','Haunted howl',oval(.54,1)),
('razor','Razor smile',[[-1,.6],[-.6,.15],[0,-.1],[.6,.15],[1,.6],[.75,-.35],[.35,-.85],[0,-.5],[-.35,-.85],[-.75,-.35]]),
('rictus','Crooked rictus',[[-1,.2],[-.55,.6],[.1,.3],[.75,.95],[1,.7],[.65,-.25],[.2,-.55],[-.4,-.8],[-.85,-.5]])
])
BASE_MOUTHS.extend([
 ('stitches','Stitched smile',[[-1,.25],[-.75,.1],[-.7,.55],[-.55,.5],[-.5,.05],[-.1,0],[-.05,.45],[.1,.45],[.15,0],[.55,.1],[.6,.55],[.75,.6],[.8,.15],[1,.35],[.9,-.15],[.75,-.3],[.7,-.65],[.55,-.6],[.5,-.25],[.1,-.3],[.05,-.7],[-.1,-.7],[-.15,-.3],[-.5,-.2],[-.55,-.6],[-.7,-.55],[-.75,-.15],[-.95,-.1]]),
 ('batgrin','Bat grin',[[-1,.75],[-.7,.1],[-.35,.4],[0,.05],[.35,.4],[.7,.1],[1,.75],[.75,-.65],[.35,-.35],[0,-.85],[-.35,-.35],[-.75,-.65]]),
 ('slashmouth','Slashed grin',[[-1,.05],[-.55,.3],[.05,.15],[.65,.65],[1,.9],[.75,.1],[.1,-.4],[-.55,-.35]]),
 ('wail','Wailing mouth',[[-.25,1],[.3,1],[.65,.3],[.6,-.5],[.25,-1],[-.3,-.9],[-.65,-.3],[-.55,.4]]),
 ('fangjaw','Fanged jaw',[[-1,.6],[-.7,.8],[-.45,-.05],[-.2,.65],[.2,.65],[.45,-.05],[.7,.8],[1,.6],[.75,-.55],[.25,-.8],[0,-.45],[-.25,-.8],[-.75,-.55]]),
 ('grimace','Grimace',[[-1,.2],[-.65,.7],[-.2,.9],[.4,.55],[1,.2],[.7,-.6],[.3,-.15],[-.2,-.65],[-.6,-.2],[-.85,-.6]])
])
MOUTHS=[]
for idx,(id,name,points) in enumerate(BASE_MOUTHS):
    MOUTHS.append(p(id,name,points))
    # Purposeful proportions, not random points or damaged silhouettes.
    MOUTHS.append(p(id+'-wide','Wide '+name.lower(),[[x,y*.62] for x,y in points]))
    MOUTHS.append(p(id+'-tall','Tall '+name.lower(),[[x*.72,y] for x,y in points]))
for feature in MOUTHS[48:]:feature['scary']=True
NOSES=[p('triangle','Triangle',[[-1,-1],[1,-1],[0,1]]),p('diamond','Diamond',[[0,1],[1,0],[0,-1],[-1,0]]),item('button','Button',[oval()]),p('long','Long triangle',[[-.5,-1],[.5,-1],[0,1.3]]),p('square','Square',[[-1,-1],[1,-1],[1,1],[-1,1]]),p('up','Upturned',[[-1,.6],[1,.6],[0,-1]]),p('crooked','Crooked',[[-1,-1],[.7,-.7],[.3,1.2]]),item('nostrils','Nostrils',[oval(.35,.4,cx=-.55),oval(.35,.4,cx=.55)]),p('heart','Heart',EYES[13]['polygons'][0]),p('kite','Kite',[[0,1.2],[.7,-.2],[0,-1],[-.7,-.2]]),p('bean','Bean',EYES[16]['polygons'][0]),p('slit','Slit',[[-1,.15],[1,.15],[1,-.15],[-1,-.15]])]
BROWS=[p('straight','Straight',[[-1,.2],[1,.2],[1,-.2],[-1,-.2]]),p('slant','Slanted',[[-1,.8],[1,-.2],[1,-.6],[-1,.4]]),p('arch','Arch',[[-1,-.3],[-.5,.5],[0,.8],[.5,.5],[1,-.3],[.5,.1],[0,.3],[-.5,.1]]),p('surprise','High arch',[[-1,-.3],[-.5,.9],[.5,.9],[1,-.3],[.5,.4],[-.5,.4]]),p('chunky','Chunky',[[-1,.5],[1,.5],[1,-.5],[-1,-.5]]),p('point','Pointed',[[-1,-.1],[0,.7],[1,-.1],[0,.2]]),p('soft','Soft',EYES[23]['polygons'][0]),p('crook','Crooked',[[-1,.3],[-.2,.1],[.3,.5],[1,.3],[1,-.1],[.3,.1],[-.2,-.3],[-1,-.1]])]
EXTRAS=[p('scar','Scar',[[-.7,1],[.7,-.6],[.4,-.9],[-1,.7]]),p('freckle','Freckle',oval()),p('star','Star',EYES[12]['polygons'][0]),p('heart','Heart',EYES[13]['polygons'][0]),p('tear','Tear',EYES[17]['polygons'][0]),item('dots','Three freckles',[oval(.2,.2,cx=-.6),oval(.2,.2,cy=.3),oval(.2,.2,cx=.6)]),p('spark','Spark',EYES[19]['polygons'][0]),p('diamond','Diamond',EYES[2]['polygons'][0])]
BODIES=[dict(id=id,name=name,sx=sx,sy=sy,ribs=ribs,bulge=b) for id,name,sx,sy,ribs,b in [('classic','Classic',1.04,.93,8,0),('tall','Tall',.82,1.22,10,0),('squat','Squat',1.16,.78,10,0),('round','Round',1,1,8,0),('pear','Pear',.95,1.13,9,-.22),('topheavy','Top heavy',1,1.08,11,.2),('mini','Mini',.9,.82,12,0),('lumpy','Lumpy',1.08,.96,7,.12)]]
STEMS=[dict(id=id,name=name) for id,name in [('stub','Little stump'),('tall','Tall stalk'),('crook','Crooked'),('curl','Curly'),('lean','Leaning'),('wide','Chunky')]]
LIDS=[dict(id=id,name=name) for id,name in [('classic','Classic lid'),('low','Low lid'),('high','Deep lid'),('zigzag','Zigzag rim')]]
TEETH=[dict(id=id,name=name,top=top,bottom=bottom,pointed=pointed) for id,name,top,bottom,pointed in [('buck','Two buck teeth',2,0,False),('single','One top tooth',1,0,False),('bottom','One bottom tooth',0,1,False),('pairbottom','Bottom pair',0,2,False),('four','Four teeth',2,2,False),('fangs','Two fangs',2,0,True),('lowerfang','Lower fangs',0,2,True),('onefang','One fang',1,0,True),('comb','Top row',4,0,False),('grill','Both rows',4,4,False),('snaggle','Snaggle tooth',1,1,True),('three','Three top teeth',3,0,False)]]
BROWS.extend([
 p('furrow','Heavy furrow',[[-1,.7],[.8,-.05],[1,-.55],[-1,.1]]),
 p('brokenbrow','Broken brow',[[-1,.7],[-.3,.35],[-.15,.6],[1,-.1],[.9,-.6],[-.2,.05],[-.4,-.2],[-1,.2]]),
 p('devilbrow','Devil brow',[[-1,1],[-.6,.35],[1,-.1],[.8,-.5],[-.8,-.1]]),
 p('scowl','Deep scowl',[[-1,.6],[-.4,.5],[1,-.3],[.8,-.7],[-.5,0],[-1,.1]])
])
NOSES.extend([
 p('skullnose','Skull nose',[[-.8,.6],[0,.1],[.8,.6],[.55,-.85],[0,-.5],[-.55,-.85]]),
 p('notchnose','Notched nose',[[0,1],[-1,-1],[-.15,-.6],[.2,-1],[1,-.7]]),
 item('boneslit','Bone slits',[oval(.22,.8,cx=-.45),oval(.22,.8,cx=.45)])
])
EXTRAS.extend([
 p('crack','Lightning crack',[[-.3,1],[.2,.2],[-.1,.05],[.45,-1],[.05,-.25],[-.3,-.05]]),
 item('stitchscar','Stitch scar',[[[-.9,.12],[.9,.12],[.9,-.12],[-.9,-.12]]]+[[[x-.08,-.5],[x+.08,-.5],[x+.08,.5],[x-.08,.5]] for x in (-.55,0,.55)]),
 p('cheekslash','Cheek slash',[[-1,.7],[1,-.5],[.7,-.75],[-.9,.4]]),
 p('bonechip','Bone chip',[[-.9,.7],[.8,.3],[.3,-.8],[-.25,-.25],[-.8,-.7]]),
 item('triplescar','Triple slash',[[[x-.12,.8],[x+.15,.7],[x+.35,-.8],[x+.1,-.65]] for x in (-.7,0,.7)])
])
TEETH.extend([dict(id=id,name=name,top=top,bottom=bottom,pointed=True,scary=True) for id,name,top,bottom in [
 ('longfangs','Long fangs',2,0),('doublefangs','Four fangs',2,2),('razorrow','Razor row',5,0),
 ('lowerrazor','Lower razor row',0,5),('needlegrill','Needle teeth',5,5),('onespike','Single spike',0,1)]])
for features,start in [(BROWS,8),(NOSES,12),(EXTRAS,8)]:
 for feature in features[start:]:feature['scary']=True
LIBRARY=dict(bodies=BODIES,stems=STEMS,lids=LIDS,eyes=EYES,brows=BROWS,noses=NOSES,mouths=MOUTHS,teeth=TEETH,extras=EXTRAS)

def component(feature,x=0,y=0,sx=1,sy=1,rotation=0):return dict(feature=feature,x=x,y=y,sx=sx,sy=sy,rotation=rotation,visible=True)
def default_design():
    return dict(version=2,id=None,name='Sir Spooks-a-Lot',body='classic',stem='crook',lid='classic',size=30,color='#ff8200',lit=False,cuts=[],parts={
    'eyeL':component(None,-.26,.67,.13,.13),'eyeR':component(None,.26,.67,.13,.13),
    'browL':component(None,-.28,.80,.18,.07),'browR':component(None,.28,.80,.18,.07),
    'nose':component(None,0,.12,.10,.12),'mouth':component(None,0,-.12,.59,.57),
    'teeth':component(None,0,0,1,1),'extraL':component(None,-.65,-.1,.08,.12),'extraR':component(None,.65,-.1,.08,.12)})

PART_LIBRARY={'eyeL':'eyes','eyeR':'eyes','browL':'brows','browR':'brows','nose':'noses','mouth':'mouths','extraL':'extras','extraR':'extras'}

def transformed(part,poly,mirror=False):
    a=math.radians(part['rotation']);c,s=math.cos(a),math.sin(a)
    result=[]
    for px,py in poly:
        x=px*part['sx']*(-1 if mirror else 1);y=py*part['sy']
        result.append([x*c-y*s+part['x'],x*s+y*c+part['y']])
    return result

def face_polygons(design):
    cuts=[];teeth=[]
    for key,lib in PART_LIBRARY.items():
        part=design['parts'][key]
        if not part['feature'] or not part['visible']:continue
        feature=next(f for f in LIBRARY[lib] if f['id']==part['feature'])
        cuts.extend(transformed(part,p,key.endswith('R')) for p in feature['polygons'])
    mouth=design['parts']['mouth'];t=design['parts']['teeth']
    if mouth['feature'] and mouth['visible'] and t['feature'] and t['visible']:
        feature=next(f for f in TEETH if f['id']==t['feature'])
        for direction,count in [(1,feature['top']),(-1,feature['bottom'])]:
            for i in range(count):
                x=(i-(count-1)/2)*(.25 if count<3 else .32)+t['x']
                width=.13*t['sx'];depth=(.60 if feature['id']=='longfangs' else .35)*t['sy']
                tip=[x,direction*(1-depth)]
                local=[[x-width/2,direction*1.15],[x+width/2,direction*1.15]]
                local+= [tip] if feature['pointed'] else [[x+width/2,direction*(1-depth)],[x-width/2,direction*(1-depth)]]
                # The mouth rim is sampled, so teeth always grow from its actual boundary.
                mouth_feature=next(f for f in MOUTHS if f['id']==mouth['feature'])
                candidates=[py for poly in mouth_feature['polygons'] for px,py in poly if abs(px-x)<.40]
                rim=(max(candidates) if direction==1 else min(candidates)) if candidates else direction
                shift=rim-direction
                local=[[px,py+shift+t['y']] for px,py in local]
                teeth.append(transformed(mouth,local))
    return cuts+design['cuts'],teeth
