"""Verify a real model in memory and save only a workspace test copy.

blender --background --factory-startup --disable-autoexec MODEL.blend
--python-exit-code 1 --python tests/convert_names_real_model.py
"""

import hashlib
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import panda_tool
from panda_tool.operators.convert_names_to_english import conversion_plan
from name_conversion_checks import stored_snapshot, evaluated_geometry, assert_geometry_close, differences


def original_signature(path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def names_snapshot():
    return {
        "objects": sorted(obj.name for obj in bpy.data.objects),
        "bones": [(a.name, [b.name for b in a.bones]) for a in bpy.data.armatures],
        "keys": [(key.name, [b.name for b in key.key_blocks]) for key in bpy.data.shape_keys],
        "materials": sorted(mat.name for mat in bpy.data.materials),
    }


def main():
    original = Path(bpy.data.filepath)
    signature = original_signature(original)
    bpy.context.preferences.edit.use_global_undo = True
    panda_tool.register()
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    model_meshes = [obj for obj in bpy.context.scene.objects
                    if obj.type == "MESH" and obj.data.shape_keys]
    assert model_meshes, "No model meshes with Shape Keys found"
    for obj in model_meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = model_meshes[0]
    supplemented = "--with-driver" in sys.argv
    if supplemented:
        # The supplied Yanagi original has no Shape Key Drivers. Add a driver
        # and animation only to the in-memory test model, then establish the
        # preservation baseline. The original file is never saved.
        obj = model_meshes[0]
        keys = obj.data.shape_keys
        blink = keys.key_blocks["まばたき"]
        obj["panda_name_test_blink"] = blink.value
        driver = blink.driver_add("value").driver
        variable = driver.variables.new()
        variable.name = "value"
        variable.targets[0].id = obj
        variable.targets[0].data_path = '["panda_name_test_blink"]'
        driver.expression = "value"
        obj["panda_name_test_probe"] = 0.0
        probe = obj.driver_add('["panda_name_test_probe"]').driver
        variable = probe.variables.new()
        variable.name = "value"
        variable.targets[0].id_type = "KEY"
        variable.targets[0].id = keys
        variable.targets[0].data_path = 'key_blocks["まばたき"].value'
        probe.expression = "value"
        mouth = keys.key_blocks["あ"]
        current_frame = bpy.context.scene.frame_current
        mouth.keyframe_insert(data_path="value", frame=current_frame)
        mouth.value = 0.15
        mouth.keyframe_insert(data_path="value", frame=current_frame + 10)
        bpy.context.scene.frame_set(current_frame)
    bpy.context.view_layer.update()

    plan, conflicts = conversion_plan(bpy.context)
    counts = {category: sum(item[0] == category for item in plan)
              for category in ("BONE", "SHAPE_KEY", "MATERIAL", "OBJECT")}
    assert counts["BONE"] > 0 and counts["SHAPE_KEY"] == 52 and counts["MATERIAL"] > 0
    inverse = {destination: source for _, _, source, destination in plan}
    before = stored_snapshot()
    before_details = stored_snapshot(details=True)
    original_names = names_snapshot()
    geometry_before = evaluated_geometry()
    basis = [(key.as_pointer(), key.reference_key.name) for key in bpy.data.shape_keys]
    driver_count = sum(len(key.animation_data.drivers) if key.animation_data else 0
                       for key in bpy.data.shape_keys)
    bpy.ops.ed.undo_push(message="Before Real Model Conversion")
    assert bpy.ops.panda_tool.convert_names_to_english("EXEC_DEFAULT", True) == {"FINISHED"}
    for _, target, _, destination in plan:
        assert target.name == destination
    after = stored_snapshot(inverse)
    if before != after:
        print("DIFFERENCES", list(differences(before_details, stored_snapshot(inverse, details=True)))[:30])
    assert before == after, [category for category in before if before[category] != after[category]]
    assert_geometry_close(geometry_before, evaluated_geometry())
    assert [(key.as_pointer(), key.reference_key.name) for key in bpy.data.shape_keys] == basis

    # Check evaluated animated geometry at multiple frames on both name states.
    frame = bpy.context.scene.frame_current
    bpy.context.scene.frame_set(frame + 10)
    animated_after = evaluated_geometry()
    bpy.context.scene.frame_set(frame)
    assert conversion_plan(bpy.context)[0] == []
    second_before = stored_snapshot()
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    assert stored_snapshot() == second_before
    assert bpy.ops.ed.undo() == {"FINISHED"}
    assert names_snapshot() == original_names
    bpy.context.scene.frame_set(frame + 10)
    assert_geometry_close(animated_after, evaluated_geometry())
    bpy.context.scene.frame_set(frame)

    # Save a converted verification copy only after Undo and second-run pass.
    assert bpy.ops.panda_tool.convert_names_to_english() == {"FINISHED"}
    suffix = ".with-driver" if supplemented else ""
    output = ROOT / "dist" / ("Yanagi.name_converter_test." + bpy.app.version_string.split()[0] + suffix + ".blend")
    assert output.resolve() != original.resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    assert original_signature(original) == signature, "Original model changed"
    report = {
        "blender": bpy.app.version_string, "original": str(original),
        "original_unchanged": True, "original_sha256": signature[2],
        "original_mtime_ns": signature[1], "converted": counts, "conflicts": conflicts,
        "renamed_names": [{"category": category, "source": source, "destination": destination}
                          for category, _, source, destination in plan],
        "shape_key_drivers_preserved": driver_count, "stored_data_preserved": list(before),
        "test_driver_and_animation_added_to_copy": supplemented,
        "evaluated_geometry_preserved": True, "animation_frames_checked": [frame, frame + 10],
        "undo": "PASS", "second_run": "PASS", "copy": str(output),
    }
    report_path = output.with_suffix(".json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    panda_tool.unregister()


if __name__ == "__main__":
    main()
