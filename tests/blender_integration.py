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


def create_cube_mesh(name, center=(0.0, 0.0, 0.0)):
    x, y, z = center
    vertices = [
        (x - 1, y - 1, z - 1),
        (x + 1, y - 1, z - 1),
        (x + 1, y + 1, z - 1),
        (x - 1, y + 1, z - 1),
        (x - 1, y - 1, z + 1),
        (x + 1, y - 1, z + 1),
        (x + 1, y + 1, z + 1),
        (x - 1, y + 1, z + 1),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    return mesh


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def assert_no_apply_modifier_temporary_data():
    assert not any(
        obj.name.startswith("PandaApplyModifierTemp") for obj in bpy.data.objects
    )
    assert not any(
        mesh.name.startswith("PandaApplyModifierTemp") for mesh in bpy.data.meshes
    )


def test_apply_modifier_without_shape_keys():
    mesh = create_cube_mesh("ApplyModifierNoKeysMesh")
    obj = bpy.data.objects.new("ApplyModifierNoKeys", mesh)
    bpy.context.scene.collection.objects.link(obj)
    select_only(obj)
    modifier = obj.modifiers.new("Triangulate", "TRIANGULATE")
    obj.panda_apply_modifier_name = modifier.name

    assert bpy.ops.panda.apply_modifier() == {"FINISHED"}
    assert obj.modifiers.get("Triangulate") is None
    assert obj.data.shape_keys is None
    assert len(obj.data.polygons) == 12
    assert_no_apply_modifier_temporary_data()


def test_apply_modifier_preserves_shape_keys_and_driver():
    mesh = bpy.data.meshes.new("ApplyModifierShapeKeysMesh")
    mesh.from_pydata(
        [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)],
        [],
        [(0, 1, 2, 3)],
    )
    obj = bpy.data.objects.new("ApplyModifierShapeKeys", mesh)
    bpy.context.scene.collection.objects.link(obj)
    select_only(obj)

    basis = obj.shape_key_add(name="Basis")
    smile = obj.shape_key_add(name="Smile")
    blink = obj.shape_key_add(name="Blink")
    smile.data[2].co.z = 1.0
    blink.data[0].co.z = 0.5
    blink.relative_key = smile
    smile.value = 0.35
    smile.slider_min = -1.0
    smile.slider_max = 2.0
    smile.mute = True
    obj.vertex_groups.new(name="Face")
    smile.vertex_group = "Face"
    mesh.shape_keys["panda_test"] = 42
    action = bpy.data.actions.new("ApplyModifierShapeKeyAction")
    mesh.shape_keys.animation_data_create().action = action

    driver_fcurve = blink.driver_add("value")
    driver_fcurve.driver.expression = "0.75"

    modifier = obj.modifiers.new("Subdivision", "SUBSURF")
    modifier.levels = 1
    modifier.subdivision_type = "CATMULL_CLARK"
    obj.panda_apply_modifier_name = modifier.name

    bpy.ops.ed.undo_push(message="Before Panda Apply Modifier")
    assert bpy.ops.panda.apply_modifier() == {"FINISHED"}
    keys = obj.data.shape_keys
    assert obj.modifiers.get("Subdivision") is None
    assert len(obj.data.vertices) > 4
    assert [block.name for block in keys.key_blocks] == ["Basis", "Smile", "Blink"]
    assert keys.key_blocks["Blink"].relative_key == keys.key_blocks["Smile"]
    assert math.isclose(keys.key_blocks["Smile"].value, 0.35, abs_tol=1e-6)
    assert math.isclose(keys.key_blocks["Smile"].slider_min, -1.0, abs_tol=1e-6)
    assert math.isclose(keys.key_blocks["Smile"].slider_max, 2.0, abs_tol=1e-6)
    assert keys.key_blocks["Smile"].mute
    assert keys.key_blocks["Smile"].vertex_group == "Face"
    assert keys["panda_test"] == 42
    assert keys.animation_data.action == action
    assert any(point.co.z > 0.1 for point in keys.key_blocks["Smile"].data)
    drivers = list(keys.animation_data.drivers)
    assert len(drivers) == 1
    assert drivers[0].data_path == 'key_blocks["Blink"].value'
    assert drivers[0].driver.expression == "0.75"
    assert len(bpy.data.shape_keys) == 1
    assert_no_apply_modifier_temporary_data()

    bpy.ops.ed.undo_push(message="After Panda Apply Modifier")
    bpy.ops.ed.undo()
    obj = bpy.data.objects["ApplyModifierShapeKeys"]
    assert obj.modifiers.get("Subdivision") is not None
    assert len(obj.data.vertices) == 4
    assert [block.name for block in obj.data.shape_keys.key_blocks] == [
        "Basis",
        "Smile",
        "Blink",
    ]
    assert len(bpy.data.shape_keys) == 1


def test_apply_mirror_preserves_asymmetric_shape():
    mesh = bpy.data.meshes.new("ApplyModifierMirrorMesh")
    mesh.from_pydata(
        [(1, -1, 0), (2, -1, 0), (1, 1, 0)],
        [],
        [(0, 1, 2)],
    )
    obj = bpy.data.objects.new("ApplyModifierMirror", mesh)
    bpy.context.scene.collection.objects.link(obj)
    select_only(obj)
    obj.shape_key_add(name="Basis")
    asymmetric = obj.shape_key_add(name="Asymmetric")
    asymmetric.data[1].co.z = 1.0
    modifier = obj.modifiers.new("Mirror", "MIRROR")
    modifier.use_axis[0] = True
    modifier.use_clip = False
    modifier.use_mirror_merge = False
    obj.panda_apply_modifier_name = modifier.name

    assert bpy.ops.panda.apply_modifier() == {"FINISHED"}
    assert len(obj.data.vertices) == 6
    assert [block.name for block in obj.data.shape_keys.key_blocks] == [
        "Basis",
        "Asymmetric",
    ]
    result = obj.data.shape_keys.key_blocks["Asymmetric"]
    raised = [point.co for point in result.data if point.co.z > 0.5]
    assert len(raised) == 2
    assert {round(point.x) for point in raised} == {-2, 2}
    assert_no_apply_modifier_temporary_data()


def test_apply_modifier_topology_mismatch_is_safe():
    source_mesh = create_cube_mesh("ApplyModifierMismatchMesh")
    source = bpy.data.objects.new("ApplyModifierMismatch", source_mesh)
    bpy.context.scene.collection.objects.link(source)
    cutter_mesh = create_cube_mesh("ApplyModifierCutterMesh", center=(1.0, 0.0, 0.0))
    cutter = bpy.data.objects.new("ApplyModifierCutter", cutter_mesh)
    bpy.context.scene.collection.objects.link(cutter)
    select_only(source)

    source.shape_key_add(name="Basis")
    moved = source.shape_key_add(name="MovedAway")
    for point in moved.data:
        point.co.x += 10.0
    modifier = source.modifiers.new("Boolean", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    source.panda_apply_modifier_name = modifier.name

    original_mesh = source.data
    original_coordinates = [point.co.copy() for point in moved.data]
    try:
        result = bpy.ops.panda.apply_modifier()
    except RuntimeError as exc:
        assert "inconsistent topology" in str(exc)
    else:
        assert result == {"CANCELLED"}
    assert source.data == original_mesh
    assert source.modifiers.get("Boolean") is not None
    assert [point.co for point in source.data.shape_keys.key_blocks["MovedAway"].data] == (
        original_coordinates
    )
    assert_no_apply_modifier_temporary_data()


def create_apply_modifier_armature(name):
    armature = bpy.data.armatures.new(f"{name}Data")
    armature_object = bpy.data.objects.new(name, armature)
    bpy.context.scene.collection.objects.link(armature_object)
    select_only(armature_object)
    bpy.ops.object.mode_set(mode="EDIT")
    root = create_bone(armature.edit_bones, "Root", (0, 0, 0), (0, 1, 0))
    forearm = create_bone(
        armature.edit_bones,
        "Forearm",
        (0, 1, 0),
        (0, 2, 0),
        parent=root,
        connected=True,
    )
    create_bone(
        armature.edit_bones,
        "Hand",
        (0, 2, 0),
        (0, 3, 0),
        parent=forearm,
        connected=True,
    )
    bpy.ops.object.mode_set(mode="POSE")
    armature_object.pose.bones["Root"].rotation_mode = "XYZ"
    armature_object.pose.bones["Root"].rotation_euler.z = math.radians(12.0)
    armature_object.pose.bones["Forearm"].rotation_mode = "XYZ"
    armature_object.pose.bones["Forearm"].rotation_euler.z = math.radians(28.0)
    armature_object.pose.bones["Hand"].rotation_mode = "XYZ"
    armature_object.pose.bones["Hand"].rotation_euler.z = math.radians(-17.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    armature.pose_position = "POSE"
    bpy.context.view_layer.update()
    return armature_object


def create_apply_modifier_skinned_object(name, armature_object, parent=False):
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(
        [
            (-0.3, 0.0, 0.0),
            (0.3, 0.0, 0.0),
            (-0.3, 1.0, 0.0),
            (0.3, 1.0, 0.0),
            (-0.3, 2.0, 0.0),
            (0.3, 2.0, 0.0),
            (-0.3, 3.0, 0.0),
            (0.3, 3.0, 0.0),
        ],
        [],
        [(0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 7, 6)],
    )
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    root = obj.vertex_groups.new(name="Root")
    forearm = obj.vertex_groups.new(name="Forearm")
    hand = obj.vertex_groups.new(name="Hand")
    root.add([0, 1], 1.0, "REPLACE")
    root.add([2, 3], 0.25, "REPLACE")
    forearm.add([2, 3], 0.75, "REPLACE")
    forearm.add([4, 5], 0.4, "REPLACE")
    hand.add([4, 5], 0.6, "REPLACE")
    hand.add([6, 7], 1.0, "REPLACE")

    if parent:
        obj.parent = armature_object
        obj.parent_type = "OBJECT"
        obj.matrix_parent_inverse = armature_object.matrix_world.inverted()

    modifier = obj.modifiers.new("Armature", "ARMATURE")
    modifier.object = armature_object
    modifier.use_vertex_groups = True
    modifier.use_bone_envelopes = False
    return obj, modifier


def mesh_topology_signature(mesh):
    return (
        tuple(tuple(edge.vertices) for edge in mesh.edges),
        tuple(tuple(polygon.vertices) for polygon in mesh.polygons),
    )


def assert_coordinate_lists_close(actual, expected, message):
    assert len(actual) == len(expected), message
    for index, (actual_coordinate, expected_coordinate) in enumerate(
        zip(actual, expected)
    ):
        assert_vector_close(
            actual_coordinate,
            expected_coordinate,
            f"{message} vertex {index}",
        )


def evaluated_armature_coordinates(
    name,
    armature_object,
    coordinates,
    preserve_volume,
    parent,
):
    reference, modifier = create_apply_modifier_skinned_object(
        name,
        armature_object,
        parent=parent,
    )
    for vertex, coordinate in zip(reference.data.vertices, coordinates):
        vertex.co = coordinate
    modifier.use_deform_preserve_volume = preserve_volume
    reference.data.update()
    bpy.context.view_layer.update()
    evaluated_object = reference.evaluated_get(bpy.context.evaluated_depsgraph_get())
    evaluated_mesh = evaluated_object.to_mesh()
    try:
        result = [vertex.co.copy() for vertex in evaluated_mesh.vertices]
    finally:
        evaluated_object.to_mesh_clear()
    reference_mesh = reference.data
    bpy.data.objects.remove(reference, do_unlink=True)
    bpy.data.meshes.remove(reference_mesh)
    return result


def test_apply_armature_matches_standard_apply():
    armature_object = create_apply_modifier_armature("ApplyArmatureStandardRig")
    for preserve_volume in (False, True):
        suffix = "Preserve" if preserve_volume else "Linear"
        standard, standard_modifier = create_apply_modifier_skinned_object(
            f"ArmatureStandard{suffix}",
            armature_object,
        )
        panda, panda_modifier = create_apply_modifier_skinned_object(
            f"ArmaturePanda{suffix}",
            armature_object,
        )
        standard_modifier.use_deform_preserve_volume = preserve_volume
        panda_modifier.use_deform_preserve_volume = preserve_volume
        if preserve_volume:
            for candidate, candidate_modifier in (
                (standard, standard_modifier),
                (panda, panda_modifier),
            ):
                mask = candidate.vertex_groups.new(name="ArmatureMask")
                mask.add([0, 1, 2, 3], 1.0, "REPLACE")
                mask.add([4, 5, 6, 7], 0.4, "REPLACE")
                candidate_modifier.vertex_group = mask.name
                candidate_modifier.invert_vertex_group = True

        original_coordinates = [vertex.co.copy() for vertex in panda.data.vertices]
        select_only(standard)
        assert bpy.ops.object.modifier_apply(modifier=standard_modifier.name) == {
            "FINISHED"
        }
        select_only(panda)
        panda.panda_apply_modifier_name = panda_modifier.name
        assert bpy.ops.panda.apply_modifier() == {"FINISHED"}

        standard_coordinates = [vertex.co.copy() for vertex in standard.data.vertices]
        panda_coordinates = [vertex.co.copy() for vertex in panda.data.vertices]
        assert_coordinate_lists_close(
            panda_coordinates,
            standard_coordinates,
            f"Armature standard Apply comparison ({suffix})",
        )
        assert mesh_topology_signature(panda.data) == mesh_topology_signature(
            standard.data
        )
        assert any(
            (actual - original).length > 1e-4
            for actual, original in zip(panda_coordinates, original_coordinates)
        )
        assert panda.modifiers.get("Armature") is None
        assert_no_apply_modifier_temporary_data()

    armature_object.data.pose_position = "REST"
    standard, standard_modifier = create_apply_modifier_skinned_object(
        "ArmatureStandardRest",
        armature_object,
    )
    panda, panda_modifier = create_apply_modifier_skinned_object(
        "ArmaturePandaRest",
        armature_object,
    )
    original_coordinates = [vertex.co.copy() for vertex in panda.data.vertices]
    select_only(standard)
    assert bpy.ops.object.modifier_apply(modifier=standard_modifier.name) == {
        "FINISHED"
    }
    select_only(panda)
    panda.panda_apply_modifier_name = panda_modifier.name
    assert bpy.ops.panda.apply_modifier() == {"FINISHED"}
    standard_coordinates = [vertex.co.copy() for vertex in standard.data.vertices]
    panda_coordinates = [vertex.co.copy() for vertex in panda.data.vertices]
    assert_coordinate_lists_close(
        panda_coordinates,
        standard_coordinates,
        "Armature Rest Position standard Apply comparison",
    )
    assert_coordinate_lists_close(
        panda_coordinates,
        original_coordinates,
        "Armature Rest Position does not bake pose transforms",
    )
    armature_object.data.pose_position = "POSE"


def test_apply_armature_preserves_shape_keys_rig_and_parenting():
    armature_object = create_apply_modifier_armature("ApplyArmatureShapeRig")
    armature_object["panda_test"] = "unchanged"
    armature_action = bpy.data.actions.new("ApplyArmatureRigAction")
    armature_object.animation_data_create().action = armature_action
    constraint = armature_object.pose.bones["Hand"].constraints.new("LIMIT_ROTATION")
    constraint.name = "PandaPreservationConstraint"
    constraint.use_limit_x = True
    constraint.min_x = -0.25
    constraint.max_x = 0.25

    obj, modifier = create_apply_modifier_skinned_object(
        "ApplyArmatureShapeMesh",
        armature_object,
        parent=True,
    )
    modifier.use_deform_preserve_volume = True
    basis = obj.shape_key_add(name="Basis")
    smile = obj.shape_key_add(name="Smile")
    blink = obj.shape_key_add(name="Blink")
    smile.data[6].co.x += 0.45
    smile.data[7].co.x += 0.45
    blink.data[0].co.z += 0.3
    blink.data[1].co.z += 0.3
    blink.relative_key = smile
    smile.value = 0.35
    smile.slider_min = -1.0
    smile.slider_max = 2.0
    blink.mute = True
    smile.vertex_group = "Hand"
    obj.data.shape_keys["panda_test"] = 64
    shape_action = bpy.data.actions.new("ApplyArmatureShapeAction")
    obj.data.shape_keys.animation_data_create().action = shape_action
    driver_fcurve = blink.driver_add("value")
    driver_fcurve.driver.expression = "0.625"

    raw_coordinates = {
        block.name: [point.co.copy() for point in block.data]
        for block in obj.data.shape_keys.key_blocks
    }
    expected_coordinates = {
        name: evaluated_armature_coordinates(
            f"Expected{name}",
            armature_object,
            coordinates,
            preserve_volume=True,
            parent=True,
        )
        for name, coordinates in raw_coordinates.items()
    }

    parent_before = obj.parent
    parent_type_before = obj.parent_type
    parent_inverse_before = obj.matrix_parent_inverse.copy()
    armature_data_before = armature_object.data
    armature_matrix_before = armature_object.matrix_world.copy()
    pose_before = {
        bone.name: bone.matrix_basis.copy() for bone in armature_object.pose.bones
    }
    constraint_before = (
        constraint.name,
        constraint.use_limit_x,
        constraint.min_x,
        constraint.max_x,
    )

    select_only(obj)
    obj.panda_apply_modifier_name = modifier.name
    bpy.ops.ed.undo_push(message="Before Panda Apply Armature")
    assert bpy.ops.panda.apply_modifier() == {"FINISHED"}

    keys = obj.data.shape_keys
    assert obj.modifiers.get("Armature") is None
    assert [block.name for block in keys.key_blocks] == ["Basis", "Smile", "Blink"]
    for name, expected in expected_coordinates.items():
        actual = [point.co.copy() for point in keys.key_blocks[name].data]
        assert_coordinate_lists_close(actual, expected, f"Armature Shape Key {name}")
    assert keys.key_blocks["Blink"].relative_key == keys.key_blocks["Smile"]
    assert math.isclose(keys.key_blocks["Smile"].value, 0.35, abs_tol=1e-6)
    assert math.isclose(keys.key_blocks["Smile"].slider_min, -1.0, abs_tol=1e-6)
    assert math.isclose(keys.key_blocks["Smile"].slider_max, 2.0, abs_tol=1e-6)
    assert keys.key_blocks["Blink"].mute
    assert keys.key_blocks["Smile"].vertex_group == "Hand"
    assert keys["panda_test"] == 64
    assert keys.animation_data.action == shape_action
    drivers = list(keys.animation_data.drivers)
    assert len(drivers) == 1
    assert drivers[0].data_path == 'key_blocks["Blink"].value'
    assert drivers[0].driver.expression == "0.625"

    assert [group.name for group in obj.vertex_groups] == ["Root", "Forearm", "Hand"]
    assert all(vertex.groups for vertex in obj.data.vertices)
    assert obj.parent == parent_before
    assert obj.parent_type == parent_type_before
    for actual_row, expected_row in zip(obj.matrix_parent_inverse, parent_inverse_before):
        assert_vector_close(actual_row, expected_row, "Parent inverse")

    assert armature_object.data == armature_data_before
    for actual_row, expected_row in zip(
        armature_object.matrix_world,
        armature_matrix_before,
    ):
        assert_vector_close(actual_row, expected_row, "Armature object matrix")
    for bone_name, expected_matrix in pose_before.items():
        for actual_row, expected_row in zip(
            armature_object.pose.bones[bone_name].matrix_basis,
            expected_matrix,
        ):
            assert_vector_close(actual_row, expected_row, f"{bone_name} pose")
    assert armature_object.animation_data.action == armature_action
    assert armature_object["panda_test"] == "unchanged"
    current_constraint = armature_object.pose.bones["Hand"].constraints[
        "PandaPreservationConstraint"
    ]
    assert (
        current_constraint.name,
        current_constraint.use_limit_x,
        current_constraint.min_x,
        current_constraint.max_x,
    ) == constraint_before
    assert_no_apply_modifier_temporary_data()

    bpy.ops.ed.undo_push(message="After Panda Apply Armature")
    bpy.ops.ed.undo()
    obj = bpy.data.objects["ApplyArmatureShapeMesh"]
    assert obj.modifiers.get("Armature") is not None
    assert [block.name for block in obj.data.shape_keys.key_blocks] == [
        "Basis",
        "Smile",
        "Blink",
    ]


def test_apply_armature_validation_is_safe():
    armature_object = create_apply_modifier_armature("ApplyArmatureValidationRig")

    missing, missing_modifier = create_apply_modifier_skinned_object(
        "ApplyArmatureMissingTarget",
        armature_object,
    )
    missing_modifier.object = None
    missing.panda_apply_modifier_name = missing_modifier.name
    missing_mesh = missing.data
    select_only(missing)
    try:
        result = bpy.ops.panda.apply_modifier()
    except RuntimeError as exc:
        assert "has no valid target" in str(exc)
    else:
        assert result == {"CANCELLED"}
    assert missing.data == missing_mesh
    assert missing.modifiers.get("Armature") is not None

    multiple, first_modifier = create_apply_modifier_skinned_object(
        "ApplyArmatureMultiple",
        armature_object,
    )
    second_modifier = multiple.modifiers.new("ArmatureSecond", "ARMATURE")
    second_modifier.object = armature_object
    multiple.panda_apply_modifier_name = first_modifier.name
    multiple_mesh = multiple.data
    select_only(multiple)
    try:
        result = bpy.ops.panda.apply_modifier()
    except RuntimeError as exc:
        assert "Multiple Armature Modifiers" in str(exc)
    else:
        assert result == {"CANCELLED"}
    assert multiple.data == multiple_mesh
    assert len([item for item in multiple.modifiers if item.type == "ARMATURE"]) == 2
    assert_no_apply_modifier_temporary_data()


def main():
    panda_tool.register()
    bpy.context.preferences.edit.use_global_undo = True

    test_apply_modifier_without_shape_keys()
    test_apply_modifier_preserves_shape_keys_and_driver()
    test_apply_mirror_preserves_asymmetric_shape()
    test_apply_modifier_topology_mismatch_is_safe()
    test_apply_armature_matches_standard_apply()
    test_apply_armature_preserves_shape_keys_rig_and_parenting()
    test_apply_armature_validation_is_safe()
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
    assert not hasattr(bpy.types.Object, "panda_apply_modifier_name")
    print("Panda Tool Blender integration test: OK")


if __name__ == "__main__":
    main()
