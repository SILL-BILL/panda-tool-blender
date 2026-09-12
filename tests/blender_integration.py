"""Run with: blender --background --python tests/blender_integration.py"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

import panda_tool


def assert_vector_close(actual, expected, message):
    expected = Vector(expected)
    if (actual - expected).length > 1e-6:
        raise AssertionError(f"{message}: {tuple(actual)} != {tuple(expected)}")


def create_bone(edit_bones, name, head, tail, parent=None, connected=False, roll=0.0):
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.parent = parent
    bone.use_connect = connected
    bone.roll = roll
    return bone


def main():
    panda_tool.register()
    bpy.context.preferences.edit.use_global_undo = True

    armature = bpy.data.armatures.new("PandaToolTestArmature")
    obj = bpy.data.objects.new("PandaToolTestArmature", armature)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    bones = armature.edit_bones
    head = create_bone(bones, "Head", (0, 0, 0), (0, 1, 0))
    hair_1 = create_bone(
        bones,
        "Hair_01",
        (0, 1, 0),
        (0, 2, 0),
        parent=head,
        connected=True,
        roll=0.37,
    )
    hair_2 = create_bone(
        bones, "Hair_02", (0, 2, 0), (0, 3, 0), parent=hair_1, connected=True
    )
    hair_r_1 = create_bone(bones, "Hair_R_01", (3, 0, 0), (4, 0, 0))
    create_bone(bones, "Hair_Anchor", (-2, 0, 0), (-2, 1, 0))

    for bone in bones:
        bone.select = False
        bone.select_head = False
        bone.select_tail = False
    for bone in (hair_1, hair_2, hair_r_1):
        bone.select = True
        bone.select_head = True
        bone.select_tail = True

    original_hair_2_head = hair_2.head.copy()
    original_hair_2_tail = hair_2.tail.copy()
    # Background mode does not initialize the undo stack automatically.
    bpy.ops.ed.undo_push(message="Before Create Anchor")
    result = bpy.ops.panda_tool.create_anchor()
    if result != {"FINISHED"}:
        raise AssertionError(f"Operator failed: {result}")

    hair_anchor = bones["Hair_Anchor.001"]
    right_anchor = bones["Hair_R_Anchor"]
    assert hair_anchor.parent == head
    assert hair_1.parent == hair_anchor and hair_1.use_connect
    assert hair_2.parent == hair_1 and hair_2.use_connect
    assert_vector_close(hair_anchor.tail, hair_1.head, "Anchor joint")
    assert_vector_close(hair_anchor.head, (0, 0.5, 0), "Anchor head")
    assert math.isclose(hair_anchor.length, 0.5, rel_tol=0.0, abs_tol=1e-6)
    assert math.isclose(hair_anchor.roll, hair_1.roll, rel_tol=0.0, abs_tol=1e-6)
    assert hair_anchor.use_deform is False
    assert_vector_close(hair_2.head, original_hair_2_head, "Child head")
    assert_vector_close(hair_2.tail, original_hair_2_tail, "Child tail")
    assert right_anchor.parent is None
    assert hair_r_1.parent == right_anchor and hair_r_1.use_connect
    assert {bone.name for bone in bones if bone.select} == {
        "Hair_Anchor.001",
        "Hair_R_Anchor",
    }
    assert bones.active == right_anchor

    # Background Python execution does not create the UI operator's automatic
    # post-operation checkpoint, so mirror that checkpoint explicitly.
    bpy.ops.ed.undo_push(message="After Create Anchor")
    bpy.ops.ed.undo()
    bones = armature.edit_bones
    assert "Hair_Anchor.001" not in bones
    assert "Hair_R_Anchor" not in bones
    assert bones["Hair_01"].parent == bones["Head"]
    assert bones["Hair_01"].use_connect

    for bone in bones:
        bone.select = False
        bone.select_head = False
        bone.select_tail = False
    bone_count = len(bones)
    assert bpy.ops.panda_tool.create_anchor() == {"CANCELLED"}
    assert len(bones) == bone_count

    bpy.ops.object.mode_set(mode="OBJECT")
    try:
        result = bpy.ops.panda_tool.create_anchor()
    except RuntimeError as exc:
        # ERROR reports from a cancelled operator are exceptions through the
        # Python API, while the UI displays the report normally.
        assert "Select an armature in Edit Mode." in str(exc)
    else:
        assert result == {"CANCELLED"}
    assert len(armature.bones) == bone_count

    print("Panda Tool Blender integration test: OK")


if __name__ == "__main__":
    main()
