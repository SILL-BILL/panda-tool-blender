"""Validate all 26 official Material mappings and preserve Material data."""

import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import panda_tool
from convert_names_integration import create_mesh, select
from name_conversion_checks import stored_snapshot, properties, action_curves
from panda_tool.operators.convert_names_to_english import conversion_plan
from test_material_dictionary import MATERIAL_MAPPING


def asset_snapshot():
    return {
        "images": [(image.as_pointer(), image.name, properties(image), list(image.pixels))
                   for image in bpy.data.images],
        "textures": [(texture.as_pointer(), texture.name, properties(texture))
                     for texture in bpy.data.textures],
    }


def fixture(source):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.edit.use_global_undo = True
    obj = create_mesh("MaterialUpdateMesh")
    material = bpy.data.materials.new(source)
    material.use_nodes = True
    material.diffuse_color = (0.2, 0.3, 0.4, 0.8)
    material["keep_source"] = source
    material.keyframe_insert(data_path="diffuse_color", frame=1)
    material.diffuse_color[0] = 0.6
    material.keyframe_insert(data_path="diffuse_color", frame=10)
    driver = material.driver_add("roughness").driver
    driver.expression = "value"
    variable = driver.variables.new()
    variable.name = "value"
    obj["roughness"] = 0.35
    variable.targets[0].id = obj
    variable.targets[0].data_path = '["roughness"]'
    tree = material.node_tree
    image = bpy.data.images.new("KeepImage", width=2, height=2)
    image.pixels = [0.1, 0.2, 0.3, 1.0] * 4
    node = tree.nodes.new("ShaderNodeTexImage")
    node.image = image
    bsdf = next(n for n in tree.nodes if n.type == "BSDF_PRINCIPLED")
    tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
    texture = bpy.data.textures.new("KeepTexture", type="IMAGE")
    texture.image = image
    other = bpy.data.materials.new("CustomMaterial")
    obj.data.materials.append(material)
    obj.data.materials.append(other)
    obj.data.materials.append(material)
    shared = create_mesh("UnselectedMaterialUser")
    shared.data.materials.append(material)
    select([obj])
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    return obj, material


def test_mapping(source, destination):
    obj, material = fixture(source)
    plan, conflicts = conversion_plan(bpy.context)
    assert conflicts == 0 and len(plan) == 1
    assert plan[0][0] == "MATERIAL" and plan[0][2:] == (source, destination)
    original = stored_snapshot()
    assets = asset_snapshot()
    slot_pointers = [slot.material.as_pointer() for slot in obj.material_slots]
    bpy.ops.ed.undo_push(message="Before Official Material Mapping")
    assert bpy.ops.panda_tool.convert_names_to_english("EXEC_DEFAULT", True) == {"FINISHED"}
    assert material.name == destination
    assert [slot.material.as_pointer() for slot in obj.material_slots] == slot_pointers
    assert stored_snapshot({destination: source}) == original
    assert asset_snapshot() == assets
    assert conversion_plan(bpy.context) == ([], 0)
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    assert stored_snapshot({destination: source}) == original
    bpy.context.scene.frame_set(10)
    animated_color = tuple(material.diffuse_color)
    animated_roughness = material.roughness
    bpy.context.scene.frame_set(1)
    assert bpy.ops.ed.undo() == {"FINISHED"}
    restored = bpy.data.materials[source]
    obj = bpy.data.objects["MaterialUpdateMesh"]
    assert [slot.material.name for slot in obj.material_slots] == [source, "CustomMaterial", source]
    assert restored["keep_source"] == source
    assert bpy.data.objects["UnselectedMaterialUser"].data.materials[0] == restored
    assert bpy.data.images["KeepImage"].size[:] == (2, 2)
    assert list(bpy.data.images["KeepImage"].pixels) == assets["images"][0][3]
    assert bpy.data.textures["KeepTexture"].image == bpy.data.images["KeepImage"]
    for curve in action_curves(restored.animation_data.action):
        restored.path_resolve(curve.data_path)
    bpy.context.scene.frame_set(10)
    assert tuple(restored.diffuse_color) == animated_color
    assert restored.roughness == animated_roughness
    bpy.context.scene.frame_set(1)

    # Global collision: the destination belongs to an unassigned Material.
    bpy.data.materials.new(destination)
    select([obj])
    before_collision = stored_snapshot()
    assert conversion_plan(bpy.context) == ([], 1)
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    assert stored_snapshot() == before_collision
    assert bpy.data.materials.get(destination + ".001") is None
    print("Official Material mapping, preservation, Undo, collision: PASS", source, destination)


def test_unknown_materials():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = create_mesh("UnknownMaterialMesh")
    sources = ["衣服01", "裙子", "未知材质", "CustomMaterial", "目影01", "目影_透明",
               "目影2", "ＣｕｓｔｏｍＭａｔｅｒｉａｌ"]
    for source in sources:
        obj.data.materials.append(bpy.data.materials.new(source))
    select([obj])
    original = stored_snapshot()
    assert conversion_plan(bpy.context) == ([], 0)
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    assert stored_snapshot() == original
    assert [slot.material.name for slot in obj.material_slots] == sources


if __name__ == "__main__":
    panda_tool.register()
    try:
        for source, destination in MATERIAL_MAPPING.items():
            test_mapping(source, destination)
        test_unknown_materials()
        print("Official Material dictionary: all 26 entries PASS", bpy.app.version_string)
    finally:
        panda_tool.unregister()
