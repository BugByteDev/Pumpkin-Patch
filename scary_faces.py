"""Scary face arrangements made from independently removable components."""
from library import default_design
# name, eyes, mouth, teeth, eye width/height, mouth width/height, nose
SCARY_FACES=[
 ('Razor grin','glare','razor','fangs',.21,.14,.65,.34,None),
 ('Sawtooth jack','slash','saw',None,.22,.16,.67,.34,'triangle'),
 ('The vampire','hook','snarl','fangs',.20,.20,.59,.38,None),
 ('Grinning skull','skull','skullgrin','grill',.22,.25,.53,.32,'up'),
 ('The hollow','hollow','howl',None,.21,.26,.44,.43,None),
 ('Narrow menace','needle','rictus','single',.25,.15,.66,.30,None),
 ('Classic fright','angry','grin','four',.22,.23,.63,.37,'triangle'),
 ('The banshee','teardrop','howl',None,.19,.27,.45,.47,None),
 ('Crooked fang','slash','rictus','onefang',.23,.18,.64,.38,None),
 ('Midnight snarl','glare','snarl','lowerfang',.23,.17,.64,.40,'nostrils'),
 ('Bone grin','hollow','skullgrin','comb',.22,.24,.60,.28,'up'),
 ('The watcher','needle','razor',None,.25,.12,.65,.28,None),
 ('Sharp smile','hook','saw',None,.22,.20,.64,.32,'long'),
 ('Wicked jack','angry','razor','fangs',.23,.21,.63,.35,'triangle'),
 ('The specter','skull','howl',None,.20,.25,.40,.45,None),
 ('Double bite','glare','snarl','snaggle',.22,.18,.64,.36,'nostrils')
]

SCARY_FACES.extend([
 ('Devil grin','demon','fangjaw','longfangs',.23,.21,.64,.34,'skullnose'),
 ('Stitched shut','sunken','stitches',None,.22,.24,.64,.27,None),
 ('Batwing jack','bat','batgrin','doublefangs',.24,.22,.64,.34,'triangle'),
 ('Knife smile','knife','slashmouth',None,.25,.18,.65,.31,None),
 ('Cracked skull','cracked','skullgrin','needlegrill',.21,.25,.58,.30,'boneslit'),
 ('Sickle grin','sickle','grimace','onespike',.23,.22,.65,.34,None),
 ('The wailer','hollow','wail',None,.20,.26,.42,.45,None),
 ('Razor bite','glare','snarl','razorrow',.23,.17,.65,.37,'notchnose'),
 ('Lower jaw','sunken','grimace','lowerrazor',.22,.25,.63,.35,'skullnose'),
 ('Night stalker','demon','razor','doublefangs',.24,.20,.65,.32,None),
 ('The stitched skull','skull','stitches',None,.22,.24,.62,.27,'up'),
 ('Broken jack','cracked','rictus','snaggle',.22,.23,.65,.34,'notchnose'),
 ('Silent glare','knife','flat',None,.25,.16,.62,.18,None),
 ('Deep scream','sunken','wail',None,.21,.25,.44,.46,'boneslit'),
 ('Bat fangs','bat','fangjaw','longfangs',.23,.20,.63,.35,None),
 ('The reaper','sickle','skullgrin','needlegrill',.23,.24,.61,.31,'skullnose')
])

def scary_preset(index):
    name,eyes,mouth,teeth,ew,eh,mw,mh,nose=SCARY_FACES[index]
    d=default_design();d['name']=name;p=d['parts']
    for key in ('eyeL','eyeR'):p[key].update(feature=eyes,sx=ew,sy=eh,y=.38)
    p['mouth'].update(feature=mouth,sx=mw,sy=mh,y=-.32)
    p['nose'].update(feature=nose,sx=.09,sy=.10,y=.03)
    p['teeth']['feature']=teeth
    if index>=16:
        if index in (16,23,25,28):
            for key in ('browL','browR'):p[key].update(feature='furrow',sx=.23,sy=.07,y=.69)
        if index in (20,27):p['extraL'].update(feature='crack',x=-.68,y=.02,sx=.08,sy=.22)
        if index==17:p['extraR'].update(feature='stitchscar',x=.65,y=-.1,sx=.11,sy=.12)
    if index==8:p['eyeR'].update(feature='glare',sy=.13)
    if index==15:p['eyeR']['rotation']=8
    return d
