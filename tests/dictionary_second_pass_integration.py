"""Exercise every newly adopted entry through the native Blender operator."""

import sys
from pathlib import Path
from unittest.mock import patch

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import panda_tool
from convert_names_integration import create_mesh, select
from name_conversion_checks import (
    action_curves, stored_snapshot, evaluated_geometry, assert_geometry_close,
)
from panda_tool.operators.convert_names_to_english import conversion_plan
from test_name_dictionary import SECOND_PASS_ENTRIES


def main():
    panda_tool.register()
    bpy.context.preferences.edit.use_global_undo = True
    bone_names = SECOND_PASS_ENTRIES["BONE"]
    armature = bpy.data.armatures.new("SecondPassRigData")
    rig = bpy.data.objects.new("SecondPassRig", armature)
    bpy.context.scene.collection.objects.link(rig)
    select([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    parent = None
    for index, name in enumerate(bone_names):
        bone = armature.edit_bones.new(name)
        bone.head = (0, 0, index * 0.1)
        bone.tail = (0, 0, (index + 1) * 0.1)
        bone.parent = parent
        parent = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh = create_mesh("SecondPassWeightedMesh")
    modifier = mesh.modifiers.new("KeepModifier", "ARMATURE")
    modifier.object = rig
    probes = []
    for index, name in enumerate(bone_names):
        mesh.vertex_groups.new(name=name).add([0, 1, 2], 1 / len(bone_names), "REPLACE")
        bone = rig.pose.bones[name]
        bone.rotation_mode = "XYZ"
        bone.keyframe_insert(data_path="rotation_euler", frame=1)
        bone.rotation_euler.x = 0.001
        bone.keyframe_insert(data_path="rotation_euler", frame=10)
        bone["reference_test"] = 0.125
        probe = bpy.data.objects.new(f"SecondPassProbe{index}", None)
        bpy.context.scene.collection.objects.link(probe)
        probe.parent = rig
        probe.parent_type = "BONE"
        probe.parent_bone = name
        constraint = probe.constraints.new("COPY_ROTATION")
        constraint.target = rig
        constraint.subtarget = name
        constraint.mute = True
        probe["read_rotation"] = 0.0
        driver = probe.driver_add('["read_rotation"]').driver
        driver.expression = "angle + 0 * transform"
        variable = driver.variables.new()
        variable.name = "angle"
        variable.targets[0].id = rig
        variable.targets[0].data_path = bone.path_from_id() + '["reference_test"]'
        variable = driver.variables.new()
        variable.name = "transform"
        variable.type = "TRANSFORMS"
        variable.targets[0].id = rig
        variable.targets[0].bone_target = name
        variable.targets[0].transform_type = "ROT_X"
        probes.append(probe.name)

    for name in SECOND_PASS_ENTRIES["MATERIAL"]:
        mesh.data.materials.append(bpy.data.materials.new(name))
    objects = [mesh]
    for name in SECOND_PASS_ENTRIES["OBJECT"]:
        objects.append(create_mesh(name))
    select(objects)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    plan, conflicts = conversion_plan(bpy.context)
    assert conflicts == 0
    assert {category: sum(row[0] == category for row in plan)
            for category in SECOND_PASS_ENTRIES} == {"BONE": 62, "MATERIAL": 7, "OBJECT": 8}
    inverse = {destination: source for _, _, source, destination in plan}
    before = stored_snapshot()
    geometry = evaluated_geometry()
    bpy.context.scene.frame_set(10)
    animated_geometry = evaluated_geometry()
    bpy.context.scene.frame_set(1)

    class FailedWrite:
        name = property(lambda self: "InjectedFailure", lambda self, value:
                        (_ for _ in ()).throw(RuntimeError("Second pass injected failure")))

    with patch("panda_tool.operators.convert_names_to_english.conversion_plan",
               return_value=(plan + [("OBJECT", FailedWrite(), "InjectedFailure", "Unused")], 0)):
        assert bpy.ops.panda_tool.convert_names_to_english() == {"CANCELLED"}
    assert stored_snapshot() == before
    assert_geometry_close(geometry, evaluated_geometry())
    bpy.ops.ed.undo_push(message="Before Second Pass Rename")
    assert bpy.ops.panda_tool.convert_names_to_english("EXEC_DEFAULT", True) == {"FINISHED"}
    for index, (source, destination) in enumerate(bone_names.items()):
        assert destination in armature.bones and destination in rig.pose.bones
        assert source not in armature.bones
        assert mesh.vertex_groups.get(destination) is not None
        probe = bpy.data.objects[probes[index]]
        assert probe.parent_bone == probe.constraints[0].subtarget == destination
        variables = probe.animation_data.drivers[0].driver.variables
        assert variables[0].targets[0].data_path == rig.pose.bones[destination].path_from_id() + '["reference_test"]', (source, destination, variables[0].type, variables[0].targets[0].id_type, variables[0].targets[0].data_path)
        assert variables[1].targets[0].bone_target == destination
    assert modifier.object == rig
    for curve in action_curves(rig.animation_data.action):
        rig.path_resolve(curve.data_path)
        assert any(f'["{destination}"]' in curve.data_path for destination in bone_names.values())
    assert stored_snapshot(inverse) == before
    assert_geometry_close(geometry, evaluated_geometry())
    bpy.context.scene.frame_set(10)
    assert_geometry_close(animated_geometry, evaluated_geometry())
    bpy.context.scene.frame_set(1)
    assert conversion_plan(bpy.context)[0] == []
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    assert stored_snapshot(inverse) == before
    assert bpy.ops.ed.undo() == {"FINISHED"}
    rig = bpy.data.objects["SecondPassRig"]
    for index, source in enumerate(bone_names):
        assert source in rig.data.bones and source in rig.pose.bones
        probe = bpy.data.objects[probes[index]]
        assert probe.parent_bone == probe.constraints[0].subtarget == source
        variables = probe.animation_data.drivers[0].driver.variables
        assert variables[0].targets[0].data_path == rig.pose.bones[source].path_from_id() + '["reference_test"]'
        assert variables[1].targets[0].bone_target == source
        assert bpy.data.objects["SecondPassWeightedMesh"].vertex_groups.get(source) is not None
    assert all(bpy.data.materials.get(name) for name in SECOND_PASS_ENTRIES["MATERIAL"])
    assert all(bpy.data.objects.get(name) for name in SECOND_PASS_ENTRIES["OBJECT"])
    assert_geometry_close(geometry, evaluated_geometry())
    # A valid SINGLE_PROP array read is not followed by Blender's native
    # bone rename in 4.2/5.1. Preflight must leave the entire model untouched.
    mesh = bpy.data.objects["SecondPassWeightedMesh"]
    mesh["array_probe"] = 0.0
    driver = mesh.driver_add('["array_probe"]').driver
    variable = driver.variables.new()
    variable.name = "value"
    variable.targets[0].id = rig
    variable.targets[0].data_path = rig.pose.bones["グルーブ"].path_from_id("rotation_euler") + "[0]"
    driver.expression = "value"
    select([mesh] + [bpy.data.objects[name] for name in SECOND_PASS_ENTRIES["OBJECT"]])
    before_unsafe = stored_snapshot()
    assert bpy.ops.panda_tool.convert_names_to_english() == {"CANCELLED"}
    assert stored_snapshot() == before_unsafe
    print("Second pass entries and all 62 bone references, rollback, undo, second run: PASS", bpy.app.version_string)
    panda_tool.unregister()


if __name__ == "__main__":
    main()
