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


def snapshot_bone(bone):
    return {
        "parent": bone.parent.name if bone.parent else None,
        "head": bone.head.copy(),
        "tail": bone.tail.copy(),
        "roll": bone.roll,
        "name": bone.name,
    }


def assert_bone_snapshot(bone, expected):
    assert (bone.parent.name if bone.parent else None) == expected["parent"]
    assert_vector_close(bone.head, expected["head"], f"{bone.name} head")
    assert_vector_close(bone.tail, expected["tail"], f"{bone.name} tail")
    assert math.isclose(bone.roll, expected["roll"], rel_tol=0.0, abs_tol=1e-6)
    assert bone.name == expected["name"]


def test_disconnect_bones():
    armature = bpy.data.armatures.new("DisconnectBonesTestArmature")
    obj = bpy.data.objects.new("DisconnectBonesTestArmature", armature)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    bones = armature.edit_bones
    parent = create_bone(bones, "Parent", (0, 0, 0), (0, 1, 0), roll=0.1)
    child_a = create_bone(
        bones, "ChildA", (0, 1, 0), (0, 2, 0), parent=parent,
        connected=True, roll=0.2
    )
    child_b = create_bone(
        bones, "ChildB", (0, 2, 0), (0, 3, 0), parent=child_a,
        connected=True, roll=0.3
    )
    already_disconnected = create_bone(
        bones, "AlreadyDisconnected", (1, 1, 0), (1, 2, 0), parent=parent,
        connected=False, roll=0.4
    )
    unselected = create_bone(
        bones, "Unselected", (0, 3, 0), (0, 4, 0), parent=child_b,
        connected=True, roll=0.5
    )

    for bone in bones:
        bone.select = False
        bone.select_head = False
        bone.select_tail = False

    # One selected connected bone is disconnected without any other changes.
    child_a.select = True
    child_a_before = snapshot_bone(child_a)
    unselected_before = snapshot_bone(unselected)
    assert bpy.ops.panda_tool.disconnect_bones() == {"FINISHED"}
    assert child_a.use_connect is False
    assert_bone_snapshot(child_a, child_a_before)
    assert unselected.use_connect is True
    assert_bone_snapshot(unselected, unselected_before)

    # Multiple selected bones, including an already disconnected bone, finish.
    child_a.select = False
    child_b.select = True
    already_disconnected.select = True
    child_b_before = snapshot_bone(child_b)
    disconnected_before = snapshot_bone(already_disconnected)
    assert bpy.ops.panda_tool.disconnect_bones() == {"FINISHED"}
    assert child_b.use_connect is False
    assert already_disconnected.use_connect is False
    assert_bone_snapshot(child_b, child_b_before)
    assert_bone_snapshot(already_disconnected, disconnected_before)
    assert unselected.use_connect is True
    assert_bone_snapshot(unselected, unselected_before)

    # The operator cannot run outside Armature Edit Mode.
    bpy.ops.object.mode_set(mode="OBJECT")
    assert not bpy.ops.panda_tool.disconnect_bones.poll()
    try:
        bpy.ops.panda_tool.disconnect_bones()
    except RuntimeError as exc:
        assert "poll() failed" in str(exc)
    else:
        raise AssertionError("Disconnect Bones unexpectedly ran in Object Mode")
    assert armature.bones["Unselected"].use_connect is True

    bpy.ops.object.mode_set(mode="POSE")
    assert not bpy.ops.panda_tool.disconnect_bones.poll()
    try:
        bpy.ops.panda_tool.disconnect_bones()
    except RuntimeError as exc:
        assert "poll() failed" in str(exc)
    else:
        raise AssertionError("Disconnect Bones unexpectedly ran in Pose Mode")
    assert armature.bones["Unselected"].use_connect is True
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def test_remove_unused_vertex_groups():
    mesh = bpy.data.meshes.new("UnusedVertexGroupsTestMesh")
    mesh.from_pydata(
        [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
        [],
        [(0, 1, 2)],
    )
    obj = bpy.data.objects.new("UnusedVertexGroupsTestMesh", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    used = obj.vertex_groups.new(name="Used")
    used.add([0], 1.0, "REPLACE")
    tiny_weight = obj.vertex_groups.new(name="TinyWeight")
    tiny_weight.add([1], 1e-12, "REPLACE")
    zero_weight = obj.vertex_groups.new(name="ZeroWeight")
    zero_weight.add([2], 0.0, "REPLACE")
    obj.vertex_groups.new(name="Empty")

    assert bpy.ops.panda_tool.scan_unused_vertex_groups() == {"FINISHED"}
    candidates = {
        item.group_name: item.remove
        for item in obj.panda_unused_vertex_groups
    }
    assert candidates == {"ZeroWeight": True, "Empty": True}

    # An unchecked candidate must survive and retain its choice after refresh.
    empty_item = next(
        item
        for item in obj.panda_unused_vertex_groups
        if item.group_name == "Empty"
    )
    empty_item.remove = False
    assert bpy.ops.panda_tool.remove_unused_vertex_groups() == {"FINISHED"}
    assert obj.vertex_groups.get("ZeroWeight") is None
    assert obj.vertex_groups.get("Empty") is not None
    assert obj.vertex_groups.get("Used") is not None
    assert obj.vertex_groups.get("TinyWeight") is not None
    assert len(obj.panda_unused_vertex_groups) == 1
    assert obj.panda_unused_vertex_groups[0].group_name == "Empty"
    assert obj.panda_unused_vertex_groups[0].remove is False

    # A candidate that gains weight after scanning is protected by the
    # immediate pre-removal re-scan.
    obj.panda_unused_vertex_groups[0].remove = True
    obj.vertex_groups["Empty"].add([2], 0.5, "REPLACE")
    assert bpy.ops.panda_tool.remove_unused_vertex_groups() == {"CANCELLED"}
    assert obj.vertex_groups.get("Empty") is not None
    assert len(obj.panda_unused_vertex_groups) == 0
    assert not bpy.ops.panda_tool.remove_unused_vertex_groups.poll()

    obj.vertex_groups.new(name="UndoEmpty")
    assert bpy.ops.panda_tool.scan_unused_vertex_groups() == {"FINISHED"}
    bpy.ops.ed.undo_push(message="Before Remove Unused Vertex Groups")
    assert bpy.ops.panda_tool.remove_unused_vertex_groups() == {"FINISHED"}
    assert obj.vertex_groups.get("UndoEmpty") is None
    # Background mode needs the UI operator's post-operation checkpoint
    # mirrored explicitly before testing Undo.
    bpy.ops.ed.undo_push(message="After Remove Unused Vertex Groups")
    bpy.ops.ed.undo()
    obj = bpy.data.objects["UnusedVertexGroupsTestMesh"]
    assert obj.vertex_groups.get("UndoEmpty") is not None

    obj.select_set(False)


def test_property_recovery_after_update():
    from panda_tool.operators.remove_unused_vertex_groups import (
        unregister_properties,
    )

    mesh = bpy.data.meshes.new("PropertyRecoveryTestMesh")
    mesh.from_pydata([(0, 0, 0)], [], [])
    obj = bpy.data.objects.new("PropertyRecoveryTestMesh", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.vertex_groups.new(name="Empty")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Simulate the old extension unregistering properties after the new
    # extension has registered its classes and panels.
    unregister_properties()
    assert not hasattr(bpy.types.Object, "panda_vertex_group_scan_complete")
    assert not bpy.ops.panda_tool.remove_unused_vertex_groups.poll()
    assert bpy.ops.panda_tool.scan_unused_vertex_groups() == {"FINISHED"}
    assert hasattr(bpy.types.Object, "panda_vertex_group_scan_complete")
    assert obj.panda_vertex_group_scan_complete
    assert obj.panda_unused_vertex_groups[0].group_name == "Empty"
    obj.select_set(False)


def test_delete_unregistered_bones():
    armature = bpy.data.armatures.new("BoneCleanupTestArmature")
    armature_obj = bpy.data.objects.new("BoneCleanupTestArmature", armature)
    bpy.context.scene.collection.objects.link(armature_obj)
    bpy.context.view_layer.objects.active = armature_obj
    armature_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    bones = armature.edit_bones
    root = create_bone(bones, "Root", (0, 0, 0), (0, 1, 0), roll=0.1)
    doomed_parent = create_bone(
        bones,
        "DoomedParent",
        (0, 1, 0),
        (0, 2, 0),
        parent=root,
        connected=True,
        roll=0.2,
    )
    surviving_child = create_bone(
        bones,
        "SurvivingChild",
        (0, 2, 0),
        (0.4, 3, 0),
        parent=doomed_parent,
        connected=True,
        roll=0.3,
    )
    connected_keep = create_bone(
        bones,
        "ConnectedKeep",
        (0, 1, 0),
        (1, 2, 0),
        parent=root,
        connected=True,
        roll=0.4,
    )
    non_deform = create_bone(
        bones,
        "NonDeformControl",
        (2, 0, 0),
        (2, 1, 0),
        roll=0.5,
    )
    non_deform.use_deform = False
    create_bone(
        bones,
        "ProtectedAfterScan",
        (3, 0, 0),
        (3, 1, 0),
        roll=0.6,
    )
    bpy.ops.object.mode_set(mode="OBJECT")

    mesh = bpy.data.meshes.new("BoneCleanupTestMesh")
    mesh.from_pydata([(0, 0, 0)], [], [])
    mesh_obj = bpy.data.objects.new("BoneCleanupTestMesh", mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)
    modifier = mesh_obj.modifiers.new("Armature", "ARMATURE")
    modifier.object = armature_obj
    for name in ("Root", "SurvivingChild", "ConnectedKeep"):
        mesh_obj.vertex_groups.new(name=name)

    bpy.ops.object.select_all(action="DESELECT")
    armature_obj.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj

    assert bpy.ops.panda_tool.scan_unregistered_bones() == {"FINISHED"}
    candidates = {
        item.bone_name: (item.remove, item.is_deform)
        for item in mesh_obj.panda_unregistered_bones
    }
    assert candidates == {
        "DoomedParent": (True, True),
        "NonDeformControl": (False, False),
        "ProtectedAfterScan": (True, True),
    }

    assert bpy.ops.panda_tool.set_unregistered_bone_selection(select=False) == {
        "FINISHED"
    }
    assert not any(item.remove for item in mesh_obj.panda_unregistered_bones)
    assert bpy.ops.panda_tool.set_unregistered_bone_selection(select=True) == {
        "FINISHED"
    }
    assert all(item.remove for item in mesh_obj.panda_unregistered_bones)

    selected_for_deletion = {"DoomedParent", "NonDeformControl"}
    for item in mesh_obj.panda_unregistered_bones:
        item.remove = item.bone_name in selected_for_deletion or (
            item.bone_name == "ProtectedAfterScan"
        )

    # Adding a matching group after the scan must protect the bone.
    mesh_obj.vertex_groups.new(name="ProtectedAfterScan")
    child_data = armature.bones["SurvivingChild"]
    child_before = {
        "head": child_data.head_local.copy(),
        "tail": child_data.tail_local.copy(),
        "matrix": child_data.matrix_local.copy(),
    }
    child_length = child_data.length
    connected_data = armature.bones["ConnectedKeep"]
    connected_before = {
        "head": connected_data.head_local.copy(),
        "tail": connected_data.tail_local.copy(),
    }

    bpy.ops.ed.undo_push(message="Before Delete Unregistered Bones")
    assert bpy.ops.panda_tool.delete_unregistered_bones() == {"FINISHED"}
    assert "DoomedParent" not in armature.bones
    assert "NonDeformControl" not in armature.bones
    assert "ProtectedAfterScan" in armature.bones

    child = armature.bones["SurvivingChild"]
    assert child.parent == armature.bones["Root"]
    assert child.use_connect is False
    assert_vector_close(child.head_local, child_before["head"], "Reparented child head")
    assert_vector_close(child.tail_local, child_before["tail"], "Reparented child tail")
    for actual_row, expected_row in zip(child.matrix_local, child_before["matrix"]):
        assert_vector_close(actual_row, expected_row, "Reparented child matrix")
    assert math.isclose(child.length, child_length, rel_tol=0.0, abs_tol=1e-6)

    connected = armature.bones["ConnectedKeep"]
    assert connected.parent == armature.bones["Root"]
    assert connected.use_connect is True
    assert_vector_close(connected.head_local, connected_before["head"], "Connected head")
    assert_vector_close(connected.tail_local, connected_before["tail"], "Connected tail")
    assert bpy.context.view_layer.objects.active == mesh_obj
    assert {obj.name for obj in bpy.context.selected_objects} == {
        armature_obj.name,
        mesh_obj.name,
    }

    # Background mode needs a post-operation checkpoint before Undo.
    bpy.ops.ed.undo_push(message="After Delete Unregistered Bones")
    bpy.ops.ed.undo()
    armature = bpy.data.armatures["BoneCleanupTestArmature"]
    assert "DoomedParent" in armature.bones
    assert "NonDeformControl" in armature.bones

    bpy.ops.object.select_all(action="DESELECT")
    orphan_mesh = bpy.data.meshes.new("OrphanBoneCleanupTestMesh")
    orphan_obj = bpy.data.objects.new("OrphanBoneCleanupTestMesh", orphan_mesh)
    bpy.context.scene.collection.objects.link(orphan_obj)
    orphan_obj.select_set(True)
    bpy.context.view_layer.objects.active = orphan_obj
    assert bpy.ops.panda_tool.scan_unregistered_bones() == {"CANCELLED"}
    orphan_obj.select_set(False)


def main():
    panda_tool.register()
    bpy.context.preferences.edit.use_global_undo = True

    test_disconnect_bones()
    test_remove_unused_vertex_groups()
    test_property_recovery_after_update()
    test_delete_unregistered_bones()

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

    panda_tool.unregister()
    assert not hasattr(bpy.types.Object, "panda_unused_vertex_groups")
    assert not hasattr(bpy.types.Object, "panda_unregistered_bones")
    print("Panda Tool Blender integration test: OK")


if __name__ == "__main__":
    main()
