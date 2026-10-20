"""Blender-rendered original pumpkin icon; uses only the approved palette."""
import bpy,math,json,gzip
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/icons'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=128
scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.look='None'
scene.view_settings.exposure=0;scene.view_settings.gamma=1
palette=['#5d1e00','#b94d00','#ff5200','#ff8200','#ffbb0b','#fffc78']
def rgba(hex):
    values=[int(hex[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values)+(1,)
def material(name,colors,steps):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');links.new(em.outputs[0],out.inputs['Surface'])
    normal=nodes.new('ShaderNodeNewGeometry');dot=nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=Vector((-.65,-.7,1.0)).normalized();links.new(normal.outputs['Normal'],dot.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT'
    while len(ramp.color_ramp.elements)>1:ramp.color_ramp.elements.remove(ramp.color_ramp.elements[-1])
    for i,(color,step) in enumerate(zip(colors,steps)):
        entry=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(step)
        entry.position=step;entry.color=rgba(color)
    links.new(dot.outputs['Value'],ramp.inputs[0]);links.new(ramp.outputs['Color'],em.inputs[0]);return mat
peel=material('Pumpkin palette',['#b94d00','#ff5200','#ff8200','#ffbb0b','#fffc78'],[0,.12,.38,.80,.97])
inside=material('Carved interior',['#5d1e00'],[0])
stalk=material('Woody stalk',['#5d1e00','#b94d00'],[0,.80])
for part in json.loads(gzip.decompress((OUT/'icon-mesh.json.gz').read_bytes())):
    vertices=[(x,-z,y) for x,y,z in part['vertices']]
    mesh=bpy.data.meshes.new(part['name']);mesh.from_pydata(vertices,[],part['faces']);mesh.update()
    obj=bpy.data.objects.new(part['name'],mesh);bpy.context.collection.objects.link(obj)
    mesh.materials.append(stalk if part['name']=='stem' else peel);mesh.materials.append(inside)
    for polygon,face in zip(mesh.polygons,part['faces']):
        polygon.use_smooth=True
        if part['name']!='stem':
            centre=sum((Vector(part['vertices'][i]) for i in face),Vector())/3
            normal=sum((Vector(part['normals'][i]) for i in face),Vector())/3
            if normal.dot(centre-Vector((0,.93,0)))<0:polygon.material_index=1
    mesh.normals_split_custom_set_from_vertices([(x,-z,y) for x,y,z in part['normals']])
# A slight turn and raised viewpoint reveal the actual carved walls and tooth depth.
bpy.ops.object.camera_add(location=(2.0,-10,3.8));camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,1.08))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=2.95;scene.camera=camera
scene.render.filepath=str(OUT/'pumpkin-render.png')
scene_file=ROOT.parent.parent/'work/icon-render/pumpkin-icon.blend'
scene_file.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(scene_file))
bpy.ops.render.render(write_still=True)
print('Rendered pumpkin icon from its hollow 3D mesh')
