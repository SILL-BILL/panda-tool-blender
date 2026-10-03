"""Selection, safety and Undo checks using real Blender data.

Run with blender --background --factory-startup --python-exit-code 1
--python tests/remove_constraints_integration.py
"""

import sys
import tempfile
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import panda_tool


def add_constraints(target):
    for constraint_type in ("COPY_LOCATION", "LIMIT_ROTATION", "CHILD_OF"):
        constraint = target.constraints.new(constraint_type)
        constraint.influence = 0.37
        constraint.mute = True


def constraint_snapshot(target):
    return [(c.name, c.type, c.influence, c.mute) for c in target.constraints]


def data_snapshot(objects):
    """Record stored data, not evaluated transforms affected by constraints."""
    result = []
    for obj in objects:
        animation = obj.animation_data
        result.append((
            obj.name, obj.type, obj.parent.name if obj.parent else None,
            tuple(obj.location), tuple(obj.rotation_euler), tuple(obj.scale),
            tuple((m.name, m.type) for m in obj.modifiers),
            animation.action.as_pointer() if animation and animation.action else None,
            tuple((f.data_path, f.array_index, f.driver.expression,
                   tuple((v.name, v.type) for v in f.driver.variables))
                  for f in animation.drivers) if animation else (),
            tuple((b.name, b.parent.name if b.parent else None,
                   tuple(b.head_local), tuple(b.tail_local), b.use_connect)
                  for b in obj.data.bones) if obj.type == "ARMATURE" else (),
            tuple((b.name, tuple(b.location), tuple(b.rotation_quaternion),
                   tuple(b.scale)) for b in obj.pose.bones)
            if obj.type == "ARMATURE" else (),
        ))
    return result


def action_snapshot(action):
    if hasattr(action, "fcurves"):
        curves = action.fcurves
    else:
        curves = [f for layer in action.layers for strip in layer.strips
                  for bag in strip.channelbags for f in bag.fcurves]
    return [(f.data_path, f.array_index,
             [(tuple(k.co), tuple(k.handle_left), tuple(k.handle_right),
             k.interpolation) for k in f.keyframe_points]) for f in curves]


def select_pose_bone(bone, selected):
    # Blender 5.0 moved pose selection from Bone to PoseBone.
    if hasattr(bone, "select"):
        bone.select = selected
    else:
        bone.bone.select = selected


def select_objects(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0] if objects else None


def assert_undo(before, names):
    # The test invokes the operator with undo=True, so Blender creates the
    # same automatic checkpoint used when the sidebar button is clicked.
    assert bpy.ops.ed.undo() == {"FINISHED"}
    for name, expected in zip(names, before):
        assert constraint_snapshot(bpy.data.objects[name]) == expected


def run_tests():
    objects = []
    for name in ("ConstraintSelectedA", "ConstraintSelectedB", "ConstraintUnselected"):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([(0, 0, 0)], [], [])
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        add_constraints(obj)
        objects.append(obj)
    names = [o.name for o in objects]
    objects[0].parent = objects[2]
    objects[0].location = (1, 2, 3)
    objects[0].modifiers.new("PreservedModifier", "SUBSURF")
    objects[0].keyframe_insert(data_path="location", frame=1)
    objects[0].location.x = 4
    objects[0].keyframe_insert(data_path="location", frame=10)
    objects[0].driver_add("scale", 0).driver.expression = "1.5"
    objects[0].constraints[0].driver_add("influence").driver.expression = "0.37"
    objects[0].constraints[1].keyframe_insert(data_path="influence", frame=1)
    objects[0].constraints[1].keyframe_insert(data_path="influence", frame=10)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    action = objects[0].animation_data.action
    keys_before = action_snapshot(action)
    before = data_snapshot(objects)
    all_object_names = set(bpy.data.objects.keys())

    select_objects(objects[:1])
    assert bpy.ops.panda_tool.remove_constraints() == {"FINISHED"}
    assert len(objects[0].constraints) == 0
    assert len(objects[1].constraints) == len(objects[2].constraints) == 3
    assert data_snapshot(objects) == before
    assert action_snapshot(action) == keys_before

    add_constraints(objects[0])
    select_objects(objects[:2])
    constraints_before = [constraint_snapshot(o) for o in objects]
    bpy.ops.ed.undo_push(message="Before Remove Constraints")
    assert bpy.ops.panda_tool.remove_constraints("EXEC_DEFAULT", True) == {"FINISHED"}
    assert all(len(o.constraints) == 0 for o in objects[:2])
    assert constraint_snapshot(objects[2]) == constraints_before[2]
    assert data_snapshot(objects) == before
    assert action_snapshot(action) == keys_before
    assert set(bpy.data.objects.keys()) == all_object_names
    assert bpy.ops.panda_tool.remove_constraints() == {"FINISHED"}
    assert_undo(constraints_before, names)
    objects = [bpy.data.objects[name] for name in names]

    select_objects([])
    assert not bpy.ops.panda_tool.remove_constraints.poll()

    armature = bpy.data.armatures.new("ConstraintRig")
    rig = bpy.data.objects.new("ConstraintRig", armature)
    bpy.context.scene.collection.objects.link(rig)
    select_objects([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    assert not bpy.ops.panda_tool.remove_constraints.poll()
    parent = None
    for index, name in enumerate(("SelectedA", "SelectedB", "Unselected")):
        bone = armature.edit_bones.new(name)
        bone.head = (0, index, 0)
        bone.tail = (0, index + 1, 0)
        bone.parent = parent
        bone.use_connect = parent is not None
        parent = bone
    bpy.ops.object.mode_set(mode="POSE")
    add_constraints(rig)
    for bone in rig.pose.bones:
        add_constraints(bone)
        select_pose_bone(bone, bone.name == "SelectedA")
    rig.pose.bones["SelectedA"].constraints[0].driver_add("influence")
    rig.pose.bones["SelectedA"].constraints[1].keyframe_insert(
        data_path="influence", frame=1,
    )
    rig.pose.bones["SelectedA"].keyframe_insert(data_path="location", frame=1)
    rig.pose.bones["SelectedA"].location.x = 0.5
    rig.pose.bones["SelectedA"].keyframe_insert(data_path="location", frame=10)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    rig_action_before = action_snapshot(rig.animation_data.action)
    rig_before = data_snapshot([rig])
    object_constraints_before = constraint_snapshot(rig)
    assert bpy.ops.panda_tool.remove_constraints() == {"FINISHED"}
    assert len(rig.pose.bones["SelectedA"].constraints) == 0
    assert len(rig.pose.bones["SelectedB"].constraints) == 3
    assert len(rig.pose.bones["Unselected"].constraints) == 3
    assert data_snapshot([rig]) == rig_before
    assert constraint_snapshot(rig) == object_constraints_before
    assert action_snapshot(rig.animation_data.action) == rig_action_before

    add_constraints(rig.pose.bones["SelectedA"])
    for bone in rig.pose.bones:
        select_pose_bone(bone, bone.name != "Unselected")
    bones_before = {b.name: constraint_snapshot(b) for b in rig.pose.bones}
    bpy.ops.ed.undo_push(message="Before Pose Remove Constraints")
    assert bpy.ops.panda_tool.remove_constraints("EXEC_DEFAULT", True) == {"FINISHED"}
    assert len(rig.pose.bones["SelectedA"].constraints) == 0
    assert len(rig.pose.bones["SelectedB"].constraints) == 0
    assert constraint_snapshot(rig.pose.bones["Unselected"]) == bones_before["Unselected"]
    assert data_snapshot([rig]) == rig_before
    assert constraint_snapshot(rig) == object_constraints_before
    assert action_snapshot(rig.animation_data.action) == rig_action_before
    assert bpy.ops.panda_tool.remove_constraints() == {"FINISHED"}
    bpy.ops.ed.undo()
    rig = bpy.data.objects["ConstraintRig"]
    for bone in rig.pose.bones:
        assert constraint_snapshot(bone) == bones_before[bone.name]
    assert constraint_snapshot(rig) == object_constraints_before
    for bone in rig.pose.bones:
        select_pose_bone(bone, False)
    assert not bpy.ops.panda_tool.remove_constraints.poll()

    # Object Mode on an armature must retain every bone constraint.
    bpy.ops.object.mode_set(mode="OBJECT")
    assert bpy.ops.panda_tool.remove_constraints() == {"FINISHED"}
    for bone in rig.pose.bones:
        assert constraint_snapshot(bone) == bones_before[bone.name]

    # Multi-object Pose Mode must cover selected bones on both armatures.
    other_rig = rig.copy()
    other_rig.data = rig.data.copy()
    other_rig.name = "OtherConstraintRig"
    bpy.context.scene.collection.objects.link(other_rig)
    select_objects([rig, other_rig])
    bpy.ops.object.mode_set(mode="POSE")
    for current_rig in (rig, other_rig):
        for bone in current_rig.pose.bones:
            select_pose_bone(bone, bone.name == "SelectedA")
    assert {(b.id_data.name, b.name) for b in bpy.context.selected_pose_bones} == {
        (rig.name, "SelectedA"), (other_rig.name, "SelectedA"),
    }
    assert bpy.ops.panda_tool.remove_constraints() == {"FINISHED"}
    for current_rig in (rig, other_rig):
        assert len(current_rig.pose.bones["SelectedA"].constraints) == 0
        assert constraint_snapshot(current_rig.pose.bones["SelectedB"]) == bones_before["SelectedB"]
        assert constraint_snapshot(current_rig.pose.bones["Unselected"]) == bones_before["Unselected"]
    bpy.ops.object.mode_set(mode="OBJECT")

    # Unsupported mesh modes never remove any constraints.
    obj = bpy.data.objects[names[0]]
    select_objects([obj])
    for mode in ("EDIT", "SCULPT", "WEIGHT_PAINT"):
        bpy.ops.object.mode_set(mode=mode)
        assert not bpy.ops.panda_tool.remove_constraints.poll()
        bpy.ops.object.mode_set(mode="OBJECT")
        assert constraint_snapshot(obj) == constraints_before[0]

    # A non-editable linked target cancels the entire mixed selection.
    with tempfile.TemporaryDirectory(prefix="panda_constraints_") as directory:
        library_path = str(Path(directory) / "constraints.blend")
        bpy.data.libraries.write(library_path, {obj})
        with bpy.data.libraries.load(library_path, link=True) as (source, target):
            target.objects = [obj.name]
        linked = target.objects[0]
        bpy.context.scene.collection.objects.link(linked)
        select_objects([obj, linked])
        assert bpy.ops.panda_tool.remove_constraints() == {"CANCELLED"}
        assert constraint_snapshot(obj) == constraints_before[0]
        assert constraint_snapshot(linked) == constraints_before[0]

    print(f"Remove Constraints integration tests: OK (Blender {bpy.app.version_string})")


if __name__ == "__main__":
    panda_tool.register()
    bpy.context.preferences.edit.use_global_undo = True
    try:
        run_tests()
    finally:
        panda_tool.unregister()
