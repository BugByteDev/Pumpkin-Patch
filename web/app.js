import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
const $=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
const ink='#5d1e00',paper='#fffc78',orange='#ff8200',red='#ff5200';
const boot=await fetch('/api/library').then(r=>r.json());
const library=boot.library,base=boot.default;
let design=structuredClone(base),category='mouths',slot='mouth',mode='orbit',undo=[],redo=[],timer,revision=0,busy=false,dirty=false;
try{const cached=JSON.parse(localStorage.getItem('pumpkin-draft'));if(cached){design=await api('/api/validate',cached);}}
catch{setStatus('A previous draft could not be loaded. Starting fresh.');}
async function api(path,data,format='json'){
 const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Pumpkin-Token':boot.token},body:JSON.stringify(data)});
 if(!response.ok){let body;try{body=await response.json();}catch{}throw Error(body?.error||'The local app could not finish that request.');}
 return format==='json'?response.json():response.blob();
}
function setStatus(message){$('status').textContent=message;}
function fail(e){$('error').hidden=false;$('error').textContent=e.message;setStatus(e.message);setTimeout(()=>$('error').hidden=true,7000);}
function remember(){undo.push(JSON.stringify(design));if(undo.length>70)undo.shift();redo=[];dirty=true;updateUndo();}
function persist(){localStorage.setItem('pumpkin-draft',JSON.stringify(design));}
function changed(rebuild=true){dirty=true;persist();if(rebuild)queueModel();}
function updateUndo(){$('undo').disabled=!undo.length;$('redo').disabled=!redo.length;}
function refresh(){syncUI();changed();}
const categories=[['bodies','body'],['stems','stem'],['lids','lid'],['eyes','eyes'],['brows','brows'],['noses','nose'],['mouths','mouth'],['teeth','teeth'],['extras','extras']];
const slots={eyes:['eyeL','eyeR'],brows:['browL','browR'],noses:['nose'],mouths:['mouth'],teeth:['teeth'],extras:['extraL','extraR']};
const names={eyeL:'left eye',eyeR:'right eye',browL:'left eyebrow',browR:'right eyebrow',nose:'nose',mouth:'mouth',teeth:'teeth',extraL:'left detail',extraR:'right detail'};
const paired=()=>slots[category]?.length===2&&$('paired').checked;
const selected=()=>design.parts[slot];
function svgEl(tag,attrs={}){const e=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;}
function polygon(parent,points,attrs={}){const p=svgEl('polygon',{points:points.map(p=>p.join(',')).join(' '),...attrs});parent.append(p);return p;}
function svgBase(view='-1.4 -1.4 2.8 2.8'){return svgEl('svg',{viewBox:view,'aria-hidden':'true'});}
function partIcon(feature,cat){
 const svg=svgBase();
 if(feature.polygons){for(const p of feature.polygons)polygon(svg,p.map(([x,y])=>[x,-y]),{fill:ink});}
 else if(cat==='bodies'){
  svg.append(svgEl('ellipse',{cx:0,cy:0,rx:feature.sx*.91,ry:feature.sy*.91,fill:orange,stroke:ink,'stroke-width':.035}));
  for(const a of [-.4,.4])svg.append(svgEl('path',{d:`M ${a} -.8 Q ${a*2} 0 ${a} .8`,fill:'none',stroke:red,'stroke-width':.05}));
 }else if(cat==='stems'){
  const path={stub:'M0 .9 L0 -.5',tall:'M0 1 L0 -1',crook:'M-.3 1 L-.3 0 L.3 -.7',curl:'M-.2 1 Q-1 -1 .3 -.8 Q1 -.4 .1 -.2',lean:'M-.5 .8 L.5 -.9',wide:'M0 .8 L0 -.7'}[feature.id];
  svg.append(svgEl('path',{d:path,fill:'none',stroke:ink,'stroke-width':feature.id==='wide'?.48:.23,'stroke-linecap':'round'}));
 }else if(cat==='lids'){
  svg.append(svgEl('path',{d:feature.id==='zigzag'?'M-1 .4 L-.6 -.1 L-.2 -.6 L.4 -.5 L1 .4 L.6 .2 L.2 .5 L-.2 .2 L-.6 .5 Z':'M-1 .3 Q0 -1.2 1 .3 Z',fill:orange,stroke:ink,'stroke-width':.04}));
 }else if(cat==='teeth'){
  svg.append(svgEl('rect',{x:-1.1,y:-.85,width:2.2,height:1.7,rx:.4,fill:ink}));
  for(const [count,sign] of [[feature.top,1],[feature.bottom,-1]])for(let i=0;i<count;i++){
   const x=(i-(count-1)/2)*.4,y=sign===1?-.88:.88;
   polygon(svg,feature.pointed?[[x-.12,y],[x+.12,y],[x,y+sign*.6]]:[[x-.12,y],[x+.12,y],[x+.12,y+sign*.5],[x-.12,y+sign*.5]],{fill:paper});
  }
 }
 return svg;
}
function choose(feature){
 if(busy)return;remember();
 if(category==='bodies')design.body=feature;
 else if(category==='stems')design.stem=feature;
 else if(category==='lids')design.lid=feature;
 else{
  const targets=paired()?slots[category]:[slot];for(const key of targets){design.parts[key].feature=feature;design.parts[key].visible=true;}
 }
 syncChoices();syncControls();changed();setStatus(feature?'Part changed. Try moving or resizing it.':'Removed. A little breathing room.');
}
function syncCategories(){
 $('categories').replaceChildren();for(const [id,label]of categories){const b=document.createElement('button');b.textContent=label;b.className=category===id?'active':'';b.onclick=()=>{category=id;slot=slots[id]?.[0]||id;syncCategories();syncChoices();syncControls();};$('categories').append(b);}
}
function syncChoices(){
 $('library-title').textContent=category==='bodies'?'pick your pumpkin':category==='mouths'?'find your grin':`pick your ${categories.find(c=>c[0]===category)[1]}`;
 $('option-count').textContent=library[category].length+' styles';
 $('target-row').hidden=!slots[category];$('target').replaceChildren();
 if(slots[category])for(const key of slots[category]){const o=document.createElement('option');o.value=key;o.textContent=names[key];o.selected=key===slot;$('target').append(o);}
 $('paired').parentElement.hidden=!slots[category]||slots[category].length!==2;
 $('choices').replaceChildren();
 const chosen=category==='bodies'?design.body:category==='stems'?design.stem:category==='lids'?design.lid:selected()?.feature;
 const options=category==='bodies'?library[category]:[{id:null,name:'None / remove'},...library[category]];
 for(const f of options){const b=document.createElement('button');b.className='choice'+(chosen===f.id?' selected':'');b.setAttribute('aria-label',f.name);b.title=f.name;
  if(f.id===null){const s=document.createElement('span');s.className='choice-label';s.textContent='none ×';b.append(s);}else b.append(partIcon(f,category));
  b.onclick=()=>choose(f.id);$('choices').append(b);
 }
}
$('target').onchange=()=>{slot=$('target').value;syncChoices();syncControls();};
function syncControls(){
 $('selected-name').textContent=names[slot]||categories.find(c=>c[0]===category)?.[1];
 const p=selected();$('transform-controls').replaceChildren();
 $('remove-part').disabled=category==='bodies';$('reset-part').disabled=!p;
 $('part-tip').textContent=category==='bodies'?'The pumpkin is your base. Pick another shape on the left.':category==='stems'||category==='lids'?'Choose “none” to remove this part.':p?.feature?'Move, resize, rotate. Make it yours.':'This part is removed. Pick a style to add it.';
 if(!p)return;
 const fields=slot==='teeth'?[['x','spacing offset',-0.4,.4,.01],['y','vertical offset',-.4,.4,.01],['sx','tooth width',.25,1.9,.01],['sy','tooth length',.25,1.9,.01]]:[['x','left / right',-.95,.95,.01],['y','down / up',-.95,.95,.01],['sx','width',.025,1.05,.005],['sy','height',.025,1.05,.005],['rotation','rotation',-180,180,1]];
 for(const [key,label,min,max,step]of fields){
  const line=document.createElement('label');line.className='range-label';line.textContent=label;const out=document.createElement('output');out.textContent=key==='rotation'?p[key]+'°':Number(p[key]).toFixed(2);line.append(out);
  const input=document.createElement('input');input.type='range';Object.assign(input,{min,max,step,value:p[key],disabled:!p.feature});input.setAttribute('aria-label',label);
  input.onpointerdown=()=>remember();input.onkeydown=e=>{if(e.key.startsWith('Arrow'))remember();};
  input.oninput=()=>{const old=p[key],v=Number(input.value);p[key]=v;if(paired()){
   const other=design.parts[slots[category].find(k=>k!==slot)];other[key]=key==='x'?-v:key==='rotation'?-v:v;
  }out.textContent=key==='rotation'?v+'°':v.toFixed(2);changed();};
  $('transform-controls').append(line,input);
 }
}
$('remove-part').onclick=()=>choose(null);
$('reset-part').onclick=()=>{if(!selected())return;remember();for(const key of (paired()?slots[category]:[slot])){const feature=design.parts[key].feature;design.parts[key]=structuredClone(base.parts[key]);design.parts[key].feature=feature;}syncControls();changed();};
function syncUI(){syncCategories();syncChoices();syncControls();$('pumpkin-name').value=design.name;$('glow').checked=design.lit;$('size').value=design.size;$('size-value').textContent=design.size+' cm';syncSwatches();updateUndo();}
function syncSwatches(){
 $('swatches').replaceChildren();for(const color of ['#ff8200','#ff5200','#ffbb0b','#ff9200','#ffd524']){const b=document.createElement('button');b.style.background=color;b.setAttribute('aria-label','Peel '+color);b.className=design.color===color?'active':'';b.onclick=()=>{remember();design.color=color;syncSwatches();changed();};$('swatches').append(b);}
}
$('pumpkin-name').onfocus=()=>remember();$('pumpkin-name').oninput=()=>{design.name=$('pumpkin-name').value;changed(false);};
$('size').onpointerdown=()=>remember();$('size').oninput=()=>{design.size=Number($('size').value);$('size-value').textContent=design.size+' cm';changed(false);};
$('undo').onclick=()=>{if(!undo.length||busy)return;redo.push(JSON.stringify(design));design=JSON.parse(undo.pop());refresh();};
$('redo').onclick=()=>{if(!redo.length||busy)return;undo.push(JSON.stringify(design));design=JSON.parse(redo.pop());refresh();};
$('new').onclick=()=>{if(busy)return;remember();design=structuredClone(base);setMode('orbit');syncUI();changed();setStatus('Fresh pumpkin. Your previous draft is still one undo away.');};
// One real 3D scene, always wearing the doodle shader.
const renderer=new THREE.WebGLRenderer({canvas:$('scene'),antialias:true,alpha:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0xffd524,0);
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(34,1,.05,30);camera.position.set(0,1,5.9);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,1,0);controls.enableDamping=true;controls.minDistance=3.4;controls.maxDistance=9;controls.minPolarAngle=.18;controls.maxPolarAngle=Math.PI*.88;controls.enablePan=false;
let group=new THREE.Group();scene.add(group);let materials=[],animation=null,lastModel=null,latestPromise=Promise.resolve();
const uniforms={time:{value:0},lit:{value:design.lit?1:0}};
const vertex=`varying vec3 n; varying vec3 p; varying float interior; uniform float centerY; void main(){interior=dot(normal,position-vec3(0.,centerY,0.))<0.?1.:0.;n=normalize(normalMatrix*normal);p=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`;
const fragment=`precision highp float;varying vec3 n;varying vec3 p;varying float interior;uniform vec3 peel;uniform float time;uniform float lit;uniform float special;
void main(){vec3 brown=vec3(.365,.118,0.);vec3 amber=vec3(1.,.733,.043);vec3 orange=vec3(1.,.51,0.);vec3 pale=vec3(1.,.988,.471);vec3 red=vec3(1.,.322,0.);vec3 c=peel;
if(special>2.5){c=sin(time*8.+p.y*4.)>.2?pale:amber;}
else if(special>1.5)c=pale;
else if(special>.5)c=brown;
else{float shade=dot(normalize(n),normalize(vec3(-.7,.8,1.)));float radial=dot(normalize(vec3(p.x,p.y-1.,p.z)),normalize(vec3(p.x,p.y-1.,p.z)+vec3(.001)));bool inner=interior>.5;
if(inner){float flicker=sin(time*7.)*.12+sin(time*13.)*.06;c=lit>.5?(p.y<.8+flicker?amber:orange):brown;}
else if(shade<.12)c=red;else if(shade>.85)c=amber;else c=peel;}
gl_FragColor=vec4(c,1.);}`;
function shader(part){const m=new THREE.ShaderMaterial({uniforms:{...uniforms,peel:{value:new THREE.Color(...part.color)},centerY:{value:library.bodies.find(b=>b.id===design.body).sy},special:{value:part.name==='stem'?1:part.name==='candle'?2:part.name==='flame'?3:0}},vertexShader:vertex,fragmentShader:fragment});materials.push(m);return m;}
function disposeGroup(g){g.traverse(o=>{o.geometry?.dispose();if(o.material){(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose());}});scene.remove(g);}
function install(parts){
 disposeGroup(group);group=new THREE.Group();group.name='pumpkin';scene.add(group);materials=[];
 for(const part of parts){const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(part.vertices.flat(),3));geo.setIndex(part.faces.flat());if(part.normals)geo.setAttribute('normal',new THREE.Float32BufferAttribute(part.normals.flat(),3));else geo.computeVertexNormals();
  const mesh=new THREE.Mesh(geo,shader(part));mesh.name=part.name;mesh.userData.part=part.name;group.add(mesh);
  const outlineMat=new THREE.ShaderMaterial({side:THREE.BackSide,uniforms:{time:uniforms.time},vertexShader:`uniform float time;void main(){vec3 v=position+normal*(.008+.002*sin(position.y*23.+position.x*18.));gl_Position=projectionMatrix*modelViewMatrix*vec4(v,1.);}`,fragmentShader:`void main(){gl_FragColor=vec4(.365,.118,0.,1.);}`});
  const line=new THREE.Mesh(geo,outlineMat);line.name=part.name+'-outline';line.userData.part=part.name;group.add(line);
  // A few purposeful rib strokes replace wireframe edges.
 }
 addRibs();lastModel=parts;updateVisibility();$('loading').hidden=true;
}
function addRibs(){
 const b=library.bodies.find(b=>b.id===design.body);const split={low:.2,high:.3}[design.lid]||.25;
 const masks=featurePolygons(design).concat(design.cuts);const inside=(x,y,p)=>{let hit=false;for(let i=0,j=p.length-1;i<p.length;j=i++){const a=p[i],b=p[j];if((a[1]>y)!=(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;};
 for(let k=0;k<b.ribs;k++)for(const [name,from,to]of [['body',split*Math.PI,Math.PI-.1],['lid',.10,split*Math.PI]]){
  if(name==='lid'&&!design.lid)continue;const chunks=[[]],theta=k*Math.PI*2/b.ribs;
  for(let j=0;j<=45;j++){const phi=from+(to-from)*j/45,r=Math.sin(phi)*(1+.06*Math.cos(b.ribs*theta))*(1+b.bulge*Math.cos(phi))+.007;
   const wobble=.002*Math.sin(j*1.7+k);if(Math.cos(theta)>0&&masks.some(p=>inside(r*Math.sin(theta),Math.cos(phi),p))){if(chunks.at(-1).length)chunks.push([]);continue;}chunks.at(-1).push(new THREE.Vector3(b.sx*r*Math.sin(theta)+wobble,b.sy*(Math.cos(phi)+1),b.sx*r*Math.cos(theta)+wobble));}
  for(const pts of chunks){if(pts.length<2)continue;const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:0xff5200}));line.userData.part=name;line.name=name+'-rib';group.add(line);}
 }
}
function updateVisibility(){uniforms.lit.value=design.lit?1:0;group.children.forEach(o=>{if(['candle','flame'].includes(o.userData.part))o.visible=design.lit;});}
let requestCounter=0;
function queueModel(){clearTimeout(timer);const seq=++requestCounter;timer=setTimeout(()=>{latestPromise=loadModel(seq);},115);}
async function loadModel(seq=++requestCounter){
 try{const parts=await api('/api/model',design);if(seq===requestCounter)install(parts);}catch(e){if(seq===requestCounter){$('loading').hidden=true;fail(e);}}
}
function front(){const b=library.bodies.find(x=>x.id===design.body);controls.target.set(0,b.sy,0);camera.position.set(0,b.sy,Math.max(5.4,b.sy*5.1));controls.update();}
$('front').onclick=front;
new ResizeObserver(()=>{const w=$('stage').clientWidth,h=$('stage').clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}).observe($('stage'));
function frame(t){requestAnimationFrame(frame);uniforms.time.value=t/1000;controls.update();
 if(animation){const e=(performance.now()-animation)/1000;const lift=e<1?e*.9:e<2.5?.9:e<3.6?.9*(1-(e-2.5)/1.1):0;
  group.children.forEach(o=>{const part=o.userData.part;if(part==='lid'||part==='stem')o.position.y=lift;if(part==='candle'||part==='flame'){o.visible=e>1;o.position.y=e<2.5?Math.max(0,(2.5-e)/1.5*3):0;}});
  setStatus(e<1?'Lifting the lid…':e<2.5?'One candle, coming right up…':e<3.6?'Putting the lid back…':'Your pumpkin is ready for the night.');
  if(e>3.8){animation=null;busy=false;controls.enabled=true;document.querySelectorAll('.library,.controls,.body-controls,.name-row,.save-row,nav').forEach(e=>e.inert=false);updateVisibility();$('complete').disabled=false;persist();}
 }
 renderer.render(scene,camera);
}requestAnimationFrame(frame);
$('glow').onchange=()=>{remember();design.lit=$('glow').checked;updateVisibility();changed(false);};
$('complete').onclick=async()=>{
 if(busy)return;remember();busy=true;$('complete').disabled=true;setMode('orbit');front();design.lit=true;$('glow').checked=true;controls.enabled=false;document.querySelectorAll('.library,.controls,.body-controls,.name-row,.save-row,nav').forEach(e=>e.inert=true);animation=performance.now();changed(false);
};
// Carving and feature movement share the front of the actual 3D pumpkin.
let stroke=[],drawing=false,dragOrigin=null;
const raycaster=new THREE.Raycaster(),ndc=new THREE.Vector2();
function facePoint(e){
 const rect=$('scene').getBoundingClientRect();ndc.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(ndc,camera);
 const b=library.bodies.find(b=>b.id===design.body),r=raycaster.ray;
 const origin=new THREE.Vector3(r.origin.x/b.sx,(r.origin.y-b.sy)/b.sy,r.origin.z/b.sx),dir=new THREE.Vector3(r.direction.x/b.sx,r.direction.y/b.sy,r.direction.z/b.sx);
 const a=dir.dot(dir),bb=2*origin.dot(dir),c=origin.dot(origin)-1,disc=bb*bb-4*a*c;
 if(disc<0)return null;const t=(-bb-Math.sqrt(disc))/(2*a),p=origin.addScaledVector(dir,t);if(p.z<.15)return null;
 return [p.x,p.y,e.clientX-rect.left,e.clientY-rect.top];
}
function setMode(next){mode=next;drawing=false;stroke=[];$('draw-overlay').replaceChildren();controls.enabled=next==='orbit';$('carver-toggle').classList.toggle('tool-active',next==='carve');$('move-mode').classList.toggle('tool-active',next==='move');$('scene').style.cursor=next==='orbit'?'grab':'crosshair';$('stage-hint').textContent=next==='carve'?'draw a closed shape · release to carve':next==='move'?'drag to move the selected feature':'drag to rotate · scroll to zoom';if(next!=='orbit')front();}
$('carver-toggle').onclick=()=>{if(!busy)setMode(mode==='carve'?'orbit':'carve');};
$('move-mode').onclick=()=>{if(!busy){if(!selected()||slot==='teeth')return setStatus('Choose an eye, brow, nose, mouth, or detail to drag.');setMode(mode==='move'?'orbit':'move');}};
$('remove-cut').onclick=()=>{if(!design.cuts.length||busy)return;remember();design.cuts.pop();changed();};
$('scene').addEventListener('pointerdown',e=>{
 if(mode==='orbit'||busy)return;const point=facePoint(e);if(!point)return;drawing=true;$('scene').setPointerCapture(e.pointerId);
 if(mode==='carve')stroke=[point];else{remember();dragOrigin={point,part:structuredClone(selected())};}
},true);
$('scene').addEventListener('pointermove',e=>{
 if(!drawing)return;const point=facePoint(e);if(!point)return;
 if(mode==='carve'){
  if(stroke.length<1000&&Math.hypot(point[2]-stroke.at(-1)[2],point[3]-stroke.at(-1)[3])>3)stroke.push(point);
  $('draw-overlay').replaceChildren(svgEl('polyline',{points:stroke.map(p=>p.slice(2).join(',')).join(' '),fill:'#ffbb0b55',stroke:ink,'stroke-width':3}));
 }else if(mode==='move'&&dragOrigin){
  selected().x=Math.max(-.95,Math.min(.95,dragOrigin.part.x+point[0]-dragOrigin.point[0]));selected().y=Math.max(-.95,Math.min(.95,dragOrigin.part.y+point[1]-dragOrigin.point[1]));
  if(paired()){const other=design.parts[slots[category].find(k=>k!==slot)];other.x=-selected().x;other.y=selected().y;}syncControls();changed();
 }
},true);
$('scene').addEventListener('pointerup',e=>{
 if(!drawing)return;drawing=false;
 if(mode==='carve'){
  const poly=stroke.map(p=>p.slice(0,2));const area=Math.abs(poly.reduce((a,p,i)=>{const prev=poly[(i+poly.length-1)%poly.length];return a+prev[0]*p[1]-p[0]*prev[1];},0))/2;
  if(poly.length<5||area<.004)setStatus('Draw a larger closed shape to make a cut.');else if(design.cuts.length>=80)setStatus('This pumpkin has reached 80 custom cuts. Undo one to make room.');else{remember();design.cuts.push(poly);changed();setStatus('Custom carving added. Undo cut removes it.');}
  stroke=[];$('draw-overlay').replaceChildren();
 }
 dragOrigin=null;
},true);
$('scene').addEventListener('pointercancel',()=>{drawing=false;stroke=[];$('draw-overlay').replaceChildren();});
// Deliberate whole-face presets, including tiny eyes and very large mouths.
function makePreset(i){const d=structuredClone(base);d.id=null;d.name=['The big laugh','Buck-tooth boo','A little gasp','Cheeky grin','Sleepy pumpkin','Happy camper','Toothy smile','Round-eyed wonder','A crooked smile','Tiny grin','Two fangs','The belly laugh','Classic jack','Cross-eyed cheer','Soft smile','Tall shout','Snaggle grin','Wide awake','Tiny teeth','Cat smile','Surprised','Wink and grin','Diamond grin','The deadpan'][i];
 const p=d.parts;
 if(i<12){const eye=['tiny','round','tiny','happy','sleepy','happy','triangle','round','side','tiny','angry','tiny'][i];const mouth=['big','big','gasp','grin','laugh','laugh','grin','big','wonky','smile','laugh','wide'][i];
  for(const key of ['eyeL','eyeR']){p[key].feature=eye;p[key].sx=i===7?.15:.11;p[key].sy=i===7?.15:.10;p[key].y=.66;}
  p.mouth.feature=mouth;p.mouth.sx=.59;p.mouth.sy=['grin','smile','wonky'].includes(mouth)?.35:.56;p.mouth.y=-.14;p.teeth.feature=['buck','single',null,'bottom',null,'buck','four',null,'snaggle',null,'fangs','buck'][i];
 }else{const j=i-12;for(const key of ['eyeL','eyeR']){p[key].feature=['triangle','cross','happy','tall','round','round','tiny','happy','round','wink','diamond','sleepy'][j];p[key].sx=.16;p[key].sy=.17;p[key].y=.33;}
  p.mouth.feature=['grin','laugh','smile','big','wonky','grin','wide','cat','gasp','smirk','grin','flat'][j];p.mouth.sx=.57;p.mouth.sy=.29;p.mouth.y=-.32;p.nose.feature=j===0?'triangle':null;p.teeth.feature=['four',null,null,'buck','single',null,'buck',null,null,'bottom','fangs',null][j];
  if(j===9)p.eyeR.feature='round';
 }return d;}
function featurePolygons(d){const result=[];const lookup={eyeL:'eyes',eyeR:'eyes',browL:'brows',browR:'brows',nose:'noses',mouth:'mouths',extraL:'extras',extraR:'extras'};
 for(const [key,lib]of Object.entries(lookup)){const part=d.parts[key];if(!part.feature||!part.visible)continue;const f=library[lib].find(x=>x.id===part.feature);const a=part.rotation*Math.PI/180;for(const poly of f.polygons)result.push(poly.map(([px,py])=>{const x=px*part.sx*(key.endsWith('R')?-1:1),y=py*part.sy;return [x*Math.cos(a)-y*Math.sin(a)+part.x,x*Math.sin(a)+y*Math.cos(a)+part.y];}));}
 return result;
}
function faceSVG(d){
 const svg=svgBase('-1.25 -1.4 2.5 2.8');svg.append(svgEl('ellipse',{cx:0,cy:.05,rx:1.04,ry:1.04,fill:d.color,stroke:ink,'stroke-width':.035}));svg.append(svgEl('path',{d:'M-.05 -1 L-.06 -1.25 L.08 -1.32',stroke:ink,'stroke-width':.13,fill:'none'}));
 for(const p of featurePolygons(d))polygon(svg,p.map(([x,y])=>[x,-y]),{fill:ink});
 const m=d.parts.mouth,t=d.parts.teeth;if(m.feature&&t.feature){const f=library.teeth.find(x=>x.id===t.feature),mf=library.mouths.find(x=>x.id===m.feature);for(const [dir,count]of [[1,f.top],[-1,f.bottom]])for(let i=0;i<count;i++){
  const x=(i-(count-1)/2)*(.25)+t.x,candidates=mf.polygons.flat().filter(p=>Math.abs(p[0]-x)<.4).map(p=>p[1]);const rim=candidates.length?(dir===1?Math.max(...candidates):Math.min(...candidates)):dir;
  const top=rim+t.y,bottom=top-dir*.35*t.sy,w=.13*t.sx;const poly=f.pointed?[[x-w/2,top],[x+w/2,top],[x,bottom]]:[[x-w/2,top],[x+w/2,top],[x+w/2,bottom],[x-w/2,bottom]];
  polygon(svg,poly.map(([x,y])=>[x*m.sx+m.x,-(y*m.sy+m.y)]),{fill:d.color});
 }}return svg;
}
for(let i=0;i<24;i++){const p=makePreset(i),b=document.createElement('button');b.append(faceSVG(p));b.title=p.name;b.setAttribute('aria-label',p.name);b.onclick=()=>{if(busy)return;remember();const keep={id:design.id,body:design.body,stem:design.stem,lid:design.lid,size:design.size,color:design.color,lit:design.lit};design={...p,...keep};syncUI();changed();setStatus('Face preset applied. Every part can still be changed or removed.');};$('presets').append(b);}
$('part-tab').onclick=()=>{$('part-controls').hidden=false;$('preset-controls').hidden=true;$('part-tab').classList.add('active');$('presets-tab').classList.remove('active');};
$('presets-tab').onclick=()=>{$('part-controls').hidden=true;$('preset-controls').hidden=false;$('part-tab').classList.remove('active');$('presets-tab').classList.add('active');};
// Durable gallery, editable files, real GLB and printable vector guides.
async function download(blob,name){if(window.pywebview?.api){const bytes=new Uint8Array(await blob.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));const result=await window.pywebview.api.save_file(btoa(binary),name);if(result.error)throw Error(result.error);if(result.cancelled)throw Error('Save cancelled.');return;}const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);}
function filename(ext){return (design.name.trim().replace(/[^a-z0-9\-_ ]/gi,'').replace(/\s+/g,'-')||'pumpkin')+ext;}
$('save').onclick=async()=>{try{design=await api('/api/save',design);persist();dirty=false;setStatus('Saved to your pumpkin patch.');}catch(e){fail(e);}};
$('export-design').onclick=()=>{download(new Blob([JSON.stringify(design,null,2)],{type:'application/json'}),filename('.pumpkin'));setStatus('Editable design file saved.');};
$('import-design').onclick=()=>$('file-input').click();$('file-input').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{if(f.size>2000000)throw Error('That design file is too large.');const next=await api('/api/validate',JSON.parse(await f.text()));remember();design=next;design.id=null;refresh();setStatus('Editable pumpkin loaded.');}catch(e){fail(e);}e.target.value='';};
$('export-glb').onclick=async()=>{const b=$('export-glb');b.disabled=true;setStatus('Building your detailed hollow GLB…');try{await download(await api('/api/export',design,'blob'),filename('.glb'));setStatus('GLB exported in metres, with closed body and lid meshes.');}catch(e){fail(e);}finally{b.disabled=false;}};
$('guide').onclick=async()=>{try{await download(await api('/api/guide',design,'blob'),filename('-carving-guide.html'));setStatus('Guide downloaded. Open it in your browser to print at 100%.');}catch(e){fail(e);}};
$('open-gallery').onclick=async()=>{try{const data=await fetch('/api/gallery').then(r=>r.json());$('gallery-grid').replaceChildren();if(!data.length){const p=document.createElement('p');p.textContent='No pumpkins yet. Save your first one!';$('gallery-grid').append(p);}for(const d of data){const card=document.createElement('article');card.className='gallery-card';card.append(faceSVG(d));const name=document.createElement('h3');name.textContent=d.name||'Unnamed pumpkin';card.append(name);const open=document.createElement('button');open.textContent='open';open.onclick=()=>{remember();design=structuredClone(d);refresh();$('gallery').close();};const del=document.createElement('button');del.textContent='delete';del.onclick=async()=>{if(!confirm('Delete “'+d.name+'” from the gallery?'))return;try{await api('/api/delete',{id:d.id});card.remove();if(design.id===d.id){design.id=null;persist();}}catch(e){fail(e);}};card.append(open,del);$('gallery-grid').append(card);}$('gallery').showModal();}catch(e){fail(e);}};
$('help').onclick=()=>$('help-dialog').showModal();document.querySelectorAll('dialog .close').forEach(b=>b.onclick=()=>b.closest('dialog').close());
window.addEventListener('keydown',e=>{if(e.key==='Escape'){setMode('orbit');return;}if(['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName))return;if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();(e.shiftKey?$('redo'):$('undo')).click();}});
window.addEventListener('beforeunload',()=>persist());
syncUI();front();await loadModel();setStatus('Ready. Tiny eyes, huge mouth, plenty of possibilities.');
// Deliberate diagnostics for offline automated integration checks.
window.pumpkin={get design(){return structuredClone(design);},library,makePreset,faceSVG,get parts(){return lastModel;},get mode(){return mode;},async settled(){clearTimeout(timer);await loadModel();},get camera(){return camera.position.toArray();}};
