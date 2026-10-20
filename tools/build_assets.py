"""Author all bundled pumpkin surfaces in Blender, validate, and export GLB assets.
blender --background --python tools/build_assets.py
"""
import bpy,sys,json,math,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mesh import surface,_grid_build as build
from library import LIBRARY,default_design
OUT=ROOT/'assets';OUT.mkdir(exist_ok=True)
report=[]
for body in LIBRARY['bodies']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for nu,nv in [(96,64),(160,100)]:
        grids=[]
        for inner in (False,True):
            coords=[surface(math.tau*i/nu,math.pi*j/nv,body,inner) for j in range(nv+1) for i in range(nu)]
            mesh=bpy.data.meshes.new('carving lattice');mesh.from_pydata(coords,[],[]);mesh.update()
            grids.append([list(v.co) for v in mesh.vertices]);bpy.data.meshes.remove(mesh)
        (OUT/(body['id']+f'-{nu}x{nv}.json.gz')).write_bytes(gzip.compress(json.dumps(grids,separators=(',',':')).encode()))
    d=default_design();d['body']=body['id']
    for p in d['parts'].values():p['feature']=None
    objects=[]
    for part in build(d):
        mesh=bpy.data.meshes.new(part.name);mesh.from_pydata(part.vertices,[],part.faces);mesh.validate();mesh.update()
        obj=bpy.data.objects.new(part.name,mesh);bpy.context.collection.objects.link(obj);objects.append(obj)
        # Coordinate conversion for Blender's Z-up studio.
        for v in mesh.vertices:v.co=(v.co.x,-v.co.z,v.co.y)
        mat=bpy.data.materials.new(part.name+' palette');mat.diffuse_color=(*part.color,1);mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*part.color,1)
        bsdf.inputs['Roughness'].default_value=1;obj.data.materials.append(mat)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(body['id']+'.glb')),export_format='GLB')
    report.append(dict(body=body['id'],objects=len(objects),triangles=sum(len(o.data.polygons) for o in objects)))
# Store an editable source scene with the final pumpkin; the grids and source code rebuild every body.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'pumpkin-source.blend'))
(OUT/'build-report.json').write_text(json.dumps(report,indent=2))
print('ASSETS_BUILT',len(report))
