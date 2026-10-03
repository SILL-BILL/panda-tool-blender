"""Run with Blender --background --factory-startup --python-exit-code 1."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import panda_tool
from panda_tool.name_dictionary import NAME_ALIASES
from panda_tool.operators.convert_names_to_english import conversion_plan
from name_conversion_checks import stored_snapshot, evaluated_geometry, assert_geometry_close, differences


def select(objects):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0] if objects else None


def create_mesh(name):
    mesh = bpy.data.meshes.new(name + "Data")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 0, 1)], [], [(0, 1, 2)])
    mesh.uv_layers.new(name="UVMap")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def test_conversion_and_preservation():
    armature = bpy.data.armatures.new("TestArmatureData")
    rig = bpy.data.objects.new("骨格", armature)
    bpy.context.scene.collection.objects.link(rig)
    select([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    parent = None
    for index, name in enumerate(("首", "左臂", "UnknownBone")):
        bone = armature.edit_bones.new(name)
        bone.head = (0, 0, index)
        bone.tail = (0, 0, index + 1)
        bone.roll = 0.17
        bone.parent = parent
        bone.use_connect = parent is not None
        parent = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    body = create_mesh("身体")
    body.parent = rig
    body["untouched"] = "身体"
    body.modifiers.new("KeepArmatureName", "ARMATURE").object = rig
    group = body.vertex_groups.new(name="左臂")
    group.add([0, 1, 2], 1.0, "REPLACE")
    body.vertex_groups.new(name="UnknownGroup")
    body.shape_key_add(name="Basis")
    expected = {}
    for destination, aliases in NAME_ALIASES["SHAPE_KEY"].items():
        block = body.shape_key_add(name=aliases[0])
        block.slider_min = -0.5
        block.slider_max = 1.5
        block.data[0].co.x = 0.15
        expected[block.name] = destination
    keys = body.data.shape_keys
    unknown = body.shape_key_add(name="UnknownFace")
    unknown.relative_key = keys.key_blocks["まばたき"]
    blink = keys.key_blocks["まばたき"]
    body["blink"] = 0.3
    driver = blink.driver_add("value").driver
    variable = driver.variables.new()
    variable.name = "blink"
    variable.targets[0].id = body
    variable.targets[0].data_path = '["blink"]'
    driver.expression = "blink"
    keys.key_blocks["あ"].keyframe_insert(data_path="value", frame=1)
    keys.key_blocks["あ"].value = 0.2
    keys.key_blocks["あ"].keyframe_insert(data_path="value", frame=10)
    rig.pose.bones["左臂"].keyframe_insert(data_path="rotation_euler", frame=1)
    rig.pose.bones["左臂"].rotation_euler.y = 0.1
    rig.pose.bones["左臂"].keyframe_insert(data_path="rotation_euler", frame=10)
    external = create_mesh("UnknownObject")
    external.driver_add("location", 0).driver.expression = "value"
    variable = external.animation_data.drivers[0].driver.variables.new()
    variable.name = "value"
    variable.targets[0].id_type = "KEY"
    variable.targets[0].id = keys
    variable.targets[0].data_path = 'key_blocks["まばたき"].value'
    bone_variable = external.animation_data.drivers[0].driver.variables.new()
    bone_variable.name = "bone_rotation"
    bone_variable.type = "TRANSFORMS"
    bone_variable.targets[0].id = rig
    bone_variable.targets[0].bone_target = "左臂"
    bone_variable.targets[0].transform_type = "ROT_Y"
    external.animation_data.drivers[0].driver.expression = "value + 0 * bone_rotation"
    constraint = external.constraints.new("COPY_LOCATION")
    constraint.target = rig
    constraint.subtarget = "左臂"
    constraint.mute = True
    child = bpy.data.objects.new("BoneChild", None)
    bpy.context.scene.collection.objects.link(child)
    child.parent = rig
    child.parent_type = "BONE"
    child.parent_bone = "左臂"
    material = bpy.data.materials.new("皮肤")
    material.use_nodes = True
    material.diffuse_color = (0.2, 0.3, 0.4, 1)
    body.data.materials.append(material)
    body.data.materials.append(bpy.data.materials.new("UnknownMaterial"))
    select([body])
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    plan, conflicts = conversion_plan(bpy.context)
    assert conflicts == 0
    assert len([item for item in plan if item[0] == "SHAPE_KEY"]) == 52
    inverse = {destination: source for _, _, source, destination in plan}
    before = stored_snapshot()
    before_details = stored_snapshot(details=True)
    geometry_before = evaluated_geometry()

    class FailedWrite:
        name = property(lambda self: "FailedWrite", lambda self, value: (_ for _ in ()).throw(RuntimeError("Injected final write failure")))

    # Exercise reverse native renames after bones, animation references,
    # shape keys, materials and objects have already changed.
    with patch("panda_tool.operators.convert_names_to_english.conversion_plan",
               return_value=(plan + [("OBJECT", FailedWrite(), "FailedWrite", "Unused")], conflicts)):
        assert bpy.ops.panda_tool.convert_names_to_english() == {"CANCELLED"}
    if before != stored_snapshot():
        print("ROLLBACK DIFFERENCES", list(differences(before_details, stored_snapshot(details=True)))[:20])
    assert before == stored_snapshot()
    assert_geometry_close(geometry_before, evaluated_geometry())
    bpy.ops.ed.undo_push(message="Before Name Conversion")
    assert bpy.ops.panda_tool.convert_names_to_english("EXEC_DEFAULT", True) == {"FINISHED"}
    assert rig.name == "Armature" and body.name == "Body"
    assert material.name == "Skin"
    for source, destination in expected.items():
        assert keys.key_blocks.get(source) is None
        assert keys.key_blocks.get(destination) is not None
    assert "UnknownBone" in armature.bones and "UnknownFace" in keys.key_blocks
    assert "Basis" in keys.key_blocks
    assert body.vertex_groups.get("Arm_L") is not None
    assert constraint.subtarget == child.parent_bone == "Arm_L"
    assert external.animation_data.drivers[0].driver.variables[1].targets[0].bone_target == "Arm_L"
    assert keys.animation_data.drivers[0].data_path == 'key_blocks["Eyelid_Close"].value'
    assert external.animation_data.drivers[0].driver.variables[0].targets[0].data_path == 'key_blocks["Eyelid_Close"].value'
    after = stored_snapshot(inverse)
    if before != after:
        print("DIFFERENCES", list(differences(before_details, stored_snapshot(inverse, details=True)))[:20])
    assert before == after, {k: (before[k], after[k]) for k in before if before[k] != after[k]}
    assert_geometry_close(geometry_before, evaluated_geometry())
    assert conversion_plan(bpy.context)[0] == []
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    assert after == stored_snapshot(inverse)
    assert bpy.ops.ed.undo() == {"FINISHED"}
    body = bpy.data.objects["身体"]
    assert "左臂" in bpy.data.objects["骨格"].data.bones
    assert "まばたき" in body.data.shape_keys.key_blocks
    assert bpy.data.materials.get("皮肤") is not None
    assert body.data.shape_keys.animation_data.drivers[0].data_path == 'key_blocks["まばたき"].value'


def test_conflicts_and_basis():
    obj = create_mesh("髪")
    unselected = create_mesh("Hair")
    obj.shape_key_add(name="あ")  # A renamed reference key must be protected too.
    obj.shape_key_add(name="まばたき")
    obj.shape_key_add(name="Eyelid_Close")
    obj.shape_key_add(name="ウィンク")
    obj.shape_key_add(name="EyeSmileLeft")
    obj.data.materials.append(bpy.data.materials.new("顔"))
    bpy.data.materials.new("Face")
    select([obj])
    plan, conflicts = conversion_plan(bpy.context)
    assert conflicts == 5
    assert not plan
    before = stored_snapshot()
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    assert before == stored_snapshot()
    assert obj.name == "髪" and unselected.name == "Hair"
    assert obj.data.shape_keys.reference_key.name == "あ"
    select([])
    assert not bpy.ops.panda_tool.convert_names_to_english.poll()
    select([obj])
    bpy.ops.object.mode_set(mode="EDIT")
    assert not bpy.ops.panda_tool.convert_names_to_english.poll()
    bpy.ops.object.mode_set(mode="OBJECT")


def test_linked_and_override():
    obj = create_mesh("服")
    select([obj])
    with tempfile.TemporaryDirectory(prefix="panda_name_") as directory:
        filename = str(Path(directory) / "linked.blend")
        bpy.data.libraries.write(filename, {obj})
        with bpy.data.libraries.load(filename, link=True) as (source, target):
            target.objects = ["服"]
        linked = target.objects[0]
        bpy.context.scene.collection.objects.link(linked)
        select([obj, linked])
        before = stored_snapshot()
        assert bpy.ops.panda_tool.convert_names_to_english() == {"CANCELLED"}
        assert before == stored_snapshot()
        override = linked.override_create(remap_local_usages=False)
        bpy.context.scene.collection.objects.link(override)
        assert override.override_library is not None
        select([obj, override])
        before = stored_snapshot()
        assert bpy.ops.panda_tool.convert_names_to_english() == {"CANCELLED"}
        assert before == stored_snapshot()


def test_bone_group_conflict():
    armature = bpy.data.armatures.new("ConflictRigData")
    rig = bpy.data.objects.new("ConflictRig", armature)
    bpy.context.scene.collection.objects.link(rig)
    select([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    for index, name in enumerate(("右腕", "RightArm", "頭", "Head", "右ひざ")):
        bone = armature.edit_bones.new(name)
        bone.head = (0, 0, index)
        bone.tail = (0, 0, index + 1)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj = create_mesh("BoneConflictMesh")
    obj.modifiers.new("Armature", "ARMATURE").object = rig
    obj.vertex_groups.new(name="Knee_R").add([0], 0.8, "REPLACE")
    obj.vertex_groups.new(name="右ひざ").add([0], 0.2, "REPLACE")
    select([obj])
    assert conversion_plan(bpy.context) == ([], 4)
    before = stored_snapshot()
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    assert before == stored_snapshot()


def test_rollback():
    obj = create_mesh("顔")
    material = bpy.data.materials.new("嘴")
    obj.data.materials.append(material)
    select([obj])
    real_plan, _ = conversion_plan(bpy.context)
    assert len(real_plan) == 2

    class UnwritableTarget:
        name = property(lambda self: "顔", lambda self, value: (_ for _ in ()).throw(RuntimeError("Injected write failure")))

    # Fail the second write after a real material rename to exercise rollback.
    with patch("panda_tool.operators.convert_names_to_english.conversion_plan",
               return_value=(real_plan[:1] + [("OBJECT", UnwritableTarget(), "顔", "Face")], 0)):
        assert bpy.ops.panda_tool.convert_names_to_english() == {"CANCELLED"}
    assert material.name == "嘴" and obj.name == "顔"


if __name__ == "__main__":
    panda_tool.register()
    bpy.context.preferences.edit.use_global_undo = True
    try:
        test_conversion_and_preservation()
        test_conflicts_and_basis()
        test_bone_group_conflict()
        test_linked_and_override()
        # Real preflight guards every RNA write; rollback also has a forced
        # failure case below to ensure an applied rename is restored.
        test_rollback()
        print("Convert Names to English integration: OK", bpy.app.version_string)
    finally:
        panda_tool.unregister()
