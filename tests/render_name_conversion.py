"""Workbench before/after pixel comparison on an isolated model load."""

import hashlib
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import panda_tool

scene = bpy.context.scene
mesh = next(obj for obj in scene.objects if obj.type == "MESH" and obj.data.shape_keys)
for obj in scene.objects:
    if obj.type == "MESH" and obj != mesh:
        obj.hide_render = True
corners = [mesh.matrix_world @ Vector(corner) for corner in mesh.bound_box]
low = Vector([min(point[i] for point in corners) for i in range(3)])
high = Vector([max(point[i] for point in corners) for i in range(3)])
center = (low + high) / 2
size = max(high - low)
camera_data = bpy.data.cameras.new("NameConversionTestCamera")
camera = bpy.data.objects.new("NameConversionTestCamera", camera_data)
scene.collection.objects.link(camera)
camera.location = center + Vector((0, -size * 2, 0))
camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
camera_data.type = "ORTHO"
camera_data.ortho_scale = size * 1.15
scene.camera = camera
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
if hasattr(scene.render.image_settings, "media_type"):
    scene.render.image_settings.media_type = "IMAGE"
scene.render.image_settings.file_format = "PNG"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = False
scene.display.shading.show_cavity = False
scene.display.shading.background_type = "WORLD"
scene.world.color = (0.08, 0.08, 0.08)
scene.render.film_transparent = False
panda_tool.register()
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
images = []
version = bpy.app.version_string.split()[0]
for stage in ("before", "after"):
    if stage == "after":
        assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    filename = ROOT / "dist" / f"Yanagi.names.{version}.{stage}.png"
    scene.render.filepath = str(filename)
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(str(filename), check_existing=False)
    images.append(list(image.pixels))
assert images[0] == images[1], "Visible appearance changed after rename"
print("Before/after Workbench pixels identical:", version,
      hashlib.sha256(repr(images[0]).encode()).hexdigest())
panda_tool.unregister()
