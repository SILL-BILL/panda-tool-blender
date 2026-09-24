"""Apply one modifier while preserving an object's shape keys."""

from copy import deepcopy

import bpy
from bpy.props import StringProperty


_TEMP_OBJECT_NAME = "PandaApplyModifierTemp"
_TEMP_MESH_NAME = "PandaApplyModifierTempMesh"


def register_properties():
    if not hasattr(bpy.types.Object, "panda_apply_modifier_name"):
        bpy.types.Object.panda_apply_modifier_name = StringProperty(
            name="Modifier",
            description="Modifier to apply while preserving Shape Keys",
        )


def unregister_properties():
    if hasattr(bpy.types.Object, "panda_apply_modifier_name"):
        del bpy.types.Object.panda_apply_modifier_name


def _copy_custom_properties(source, destination):
    """Copy supported ID properties and their UI metadata."""
    if not hasattr(source, "keys") or not hasattr(destination, "keys"):
        return
    try:
        names = list(source.keys())
    except (AttributeError, TypeError):
        return
    for name in names:
        try:
            value = source[name]
            if hasattr(value, "to_dict"):
                value = value.to_dict()
            elif hasattr(value, "to_list"):
                value = value.to_list()
            else:
                value = deepcopy(value)
            destination[name] = value
            ui_data = source.id_properties_ui(name).as_dict()
            if ui_data:
                destination.id_properties_ui(name).update(**ui_data)
        except (AttributeError, KeyError, TypeError, ValueError):
            # Runtime/library properties may be read-only. Custom properties
            # are optional metadata, so geometry safety takes precedence.
            continue


def _copy_driver_target(
    source,
    destination,
    source_key,
    destination_key,
):
    for attribute in (
        "id_type",
        "id",
        "data_path",
        "bone_target",
        "transform_type",
        "transform_space",
        "rotation_mode",
    ):
        try:
            value = getattr(source, attribute)
            if attribute == "id" and value == source_key:
                value = destination_key
            setattr(destination, attribute, value)
        except (AttributeError, TypeError, ValueError):
            pass


def _copy_driver(source_fcurve, source_key, destination_key):
    try:
        destination_fcurve = destination_key.driver_add(
            source_fcurve.data_path,
            source_fcurve.array_index,
        )
    except (TypeError, ValueError):
        destination_fcurve = destination_key.driver_add(source_fcurve.data_path)

    for attribute in ("mute", "lock", "select", "extrapolation"):
        try:
            setattr(destination_fcurve, attribute, getattr(source_fcurve, attribute))
        except (AttributeError, TypeError, ValueError):
            pass

    source_driver = source_fcurve.driver
    destination_driver = destination_fcurve.driver
    destination_driver.type = source_driver.type
    destination_driver.expression = source_driver.expression
    destination_driver.use_self = source_driver.use_self

    for source_variable in source_driver.variables:
        destination_variable = destination_driver.variables.new()
        destination_variable.name = source_variable.name
        destination_variable.type = source_variable.type
        for source_target, destination_target in zip(
            source_variable.targets,
            destination_variable.targets,
        ):
            _copy_driver_target(
                source_target,
                destination_target,
                source_key,
                destination_key,
            )


def _copy_animation_data(source_key, destination_key):
    source_animation = source_key.animation_data
    if source_animation is None:
        return

    destination_animation = destination_key.animation_data_create()
    if source_animation.action is not None:
        destination_animation.action = source_animation.action
        for attribute in (
            "action_blend_type",
            "action_extrapolation",
            "action_influence",
            "use_nla",
        ):
            try:
                setattr(
                    destination_animation,
                    attribute,
                    getattr(source_animation, attribute),
                )
            except (AttributeError, TypeError, ValueError):
                pass

    for source_fcurve in source_animation.drivers:
        _copy_driver(source_fcurve, source_key, destination_key)


def _mesh_topology(mesh):
    """Return a strict topology signature independent of coordinates."""
    return (
        len(mesh.vertices),
        tuple(tuple(edge.vertices) for edge in mesh.edges),
        tuple(tuple(polygon.vertices) for polygon in mesh.polygons),
    )


def _remove_mesh_if_unused(mesh):
    if mesh is not None and mesh.users == 0:
        if mesh.shape_keys is not None:
            bpy.data.batch_remove(ids=(mesh.shape_keys, mesh))
        else:
            bpy.data.meshes.remove(mesh)


def _copy_mesh_without_shape_keys(context, source_object):
    """Copy evaluated base mesh data without duplicating the Key datablock."""
    probe_object = source_object.copy()
    probe_object.name = _TEMP_OBJECT_NAME
    context.scene.collection.objects.link(probe_object)
    try:
        for modifier in probe_object.modifiers:
            modifier.show_viewport = False
            modifier.show_render = False
        context.view_layer.update()
        depsgraph = context.evaluated_depsgraph_get()
        evaluated_object = probe_object.evaluated_get(depsgraph)
        mesh = bpy.data.meshes.new_from_object(
            evaluated_object,
            preserve_all_data_layers=True,
            depsgraph=depsgraph,
        )
        mesh.name = _TEMP_MESH_NAME
        return mesh
    finally:
        bpy.data.objects.remove(probe_object, do_unlink=True)


def _evaluate_shape(
    context,
    source_object,
    source_mesh_without_keys,
    modifier_name,
    coordinates,
):
    """Apply the modifier to a disposable copy containing one raw key shape."""
    temporary_object = source_object.copy()
    temporary_mesh = source_mesh_without_keys.copy()
    temporary_object.data = temporary_mesh
    temporary_object.name = _TEMP_OBJECT_NAME
    temporary_mesh.name = _TEMP_MESH_NAME
    context.scene.collection.objects.link(temporary_object)

    try:
        if len(temporary_mesh.vertices) != len(coordinates):
            raise RuntimeError("Source Shape Key vertex count changed unexpectedly.")
        for vertex, coordinate in zip(temporary_mesh.vertices, coordinates):
            vertex.co = coordinate
        temporary_mesh.update()

        with context.temp_override(
            object=temporary_object,
            active_object=temporary_object,
            selected_objects=[temporary_object],
            selected_editable_objects=[temporary_object],
        ):
            result = bpy.ops.object.modifier_apply(modifier=modifier_name)
        if result != {"FINISHED"}:
            raise RuntimeError("Blender could not apply the selected Modifier.")

        evaluated_mesh = temporary_object.data.copy()
        evaluated_mesh.name = _TEMP_MESH_NAME
        return evaluated_mesh
    finally:
        bpy.data.objects.remove(temporary_object, do_unlink=True)
        _remove_mesh_if_unused(temporary_mesh)


def _key_block_metadata(key_block):
    return {
        "name": key_block.name,
        "value": key_block.value,
        "slider_min": key_block.slider_min,
        "slider_max": key_block.slider_max,
        "mute": key_block.mute,
        "vertex_group": key_block.vertex_group,
        "interpolation": key_block.interpolation,
        "relative_name": (
            key_block.relative_key.name if key_block.relative_key else None
        ),
        "custom_source": key_block,
    }


def _restore_key_metadata(source_key, destination_key, metadata, new_blocks):
    destination_key.use_relative = source_key.use_relative
    destination_key.eval_time = source_key.eval_time
    destination_key.name = source_key.name
    _copy_custom_properties(source_key, destination_key)

    for key_block, item in zip(destination_key.key_blocks, metadata):
        key_block.slider_min = item["slider_min"]
        key_block.slider_max = item["slider_max"]
        key_block.mute = item["mute"]
        key_block.vertex_group = item["vertex_group"]
        key_block.interpolation = item["interpolation"]
        _copy_custom_properties(item["custom_source"], key_block)

    if source_key.use_relative:
        for key_block, item in zip(destination_key.key_blocks, metadata):
            relative_name = item["relative_name"]
            if relative_name in new_blocks:
                key_block.relative_key = new_blocks[relative_name]

    for key_block, item in zip(destination_key.key_blocks, metadata):
        key_block.value = item["value"]

    _copy_animation_data(source_key, destination_key)


class PANDA_OT_apply_modifier(bpy.types.Operator):
    """Apply one modifier without discarding Shape Keys"""

    bl_idname = "panda.apply_modifier"
    bl_label = "Apply Safely"
    bl_description = "Apply one Modifier while preserving Shape Keys"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        source_object = context.active_object
        if source_object is None:
            self.report({"ERROR"}, "Panda Apply Modifier: No active Object.")
            return {"CANCELLED"}
        if source_object.type != "MESH":
            self.report({"ERROR"}, "Panda Apply Modifier: Active Object is not a Mesh.")
            return {"CANCELLED"}
        if source_object.mode != "OBJECT":
            self.report({"ERROR"}, "Panda Apply Modifier: Use Object Mode.")
            return {"CANCELLED"}
        if not source_object.modifiers:
            self.report({"ERROR"}, "Panda Apply Modifier: Object has no Modifiers.")
            return {"CANCELLED"}

        register_properties()
        modifier_name = source_object.panda_apply_modifier_name
        modifier = source_object.modifiers.get(modifier_name)
        if modifier is None:
            self.report({"ERROR"}, "Panda Apply Modifier: Select a valid Modifier.")
            return {"CANCELLED"}
        if modifier.type == "ARMATURE":
            self.report(
                {"ERROR"},
                "Panda Apply Modifier: Armature Modifiers are not supported.",
            )
            return {"CANCELLED"}

        source_mesh = source_object.data
        source_key = source_mesh.shape_keys
        source_blocks = list(source_key.key_blocks) if source_key else []
        shape_coordinates = (
            [[point.co.copy() for point in block.data] for block in source_blocks]
            if source_blocks
            else [[vertex.co.copy() for vertex in source_mesh.vertices]]
        )
        metadata = [_key_block_metadata(block) for block in source_blocks]

        result_mesh = None
        builder_object = None
        source_mesh_without_keys = None
        expected_topology = None
        try:
            source_mesh_without_keys = _copy_mesh_without_shape_keys(
                context,
                source_object,
            )
            for index, coordinates in enumerate(shape_coordinates):
                evaluated_mesh = _evaluate_shape(
                    context,
                    source_object,
                    source_mesh_without_keys,
                    modifier_name,
                    coordinates,
                )
                try:
                    topology = _mesh_topology(evaluated_mesh)
                    if expected_topology is None:
                        expected_topology = topology
                        result_mesh = evaluated_mesh.copy()
                        result_mesh.name = f"{source_mesh.name}_PandaApplied"
                        builder_object = bpy.data.objects.new(
                            _TEMP_OBJECT_NAME,
                            result_mesh,
                        )
                        context.scene.collection.objects.link(builder_object)
                        if source_blocks:
                            builder_object.shape_key_add(
                                name=metadata[0]["name"],
                                from_mix=False,
                            )
                    elif topology != expected_topology:
                        key_name = metadata[index]["name"]
                        raise RuntimeError(
                            "Modifier evaluation produced inconsistent topology "
                            f'across Shape Keys (detected on "{key_name}").'
                        )

                    if source_blocks and index > 0:
                        new_block = builder_object.shape_key_add(
                            name=metadata[index]["name"],
                            from_mix=False,
                        )
                        if len(new_block.data) != len(evaluated_mesh.vertices):
                            raise RuntimeError(
                                "Modifier evaluation produced inconsistent vertex counts."
                            )
                        for point, vertex in zip(
                            new_block.data,
                            evaluated_mesh.vertices,
                        ):
                            point.co = vertex.co
                finally:
                    _remove_mesh_if_unused(evaluated_mesh)

            if source_blocks:
                destination_key = result_mesh.shape_keys
                new_blocks = {
                    block.name: block for block in destination_key.key_blocks
                }
                _restore_key_metadata(
                    source_key,
                    destination_key,
                    metadata,
                    new_blocks,
                )

            # This is the first mutation of the user's Object.
            source_object.data = result_mesh
            source_object.modifiers.remove(modifier)
            bpy.data.objects.remove(builder_object, do_unlink=True)
            builder_object = None
            result_mesh.name = source_mesh.name
            _remove_mesh_if_unused(source_mesh)
        except Exception as exc:
            if result_mesh is not None and source_object.data == result_mesh:
                source_object.data = source_mesh
            if builder_object is not None:
                bpy.data.objects.remove(builder_object, do_unlink=True)
            _remove_mesh_if_unused(result_mesh)
            self.report(
                {"ERROR"},
                f"Panda Apply Modifier: {exc} Operation cancelled.",
            )
            return {"CANCELLED"}
        finally:
            _remove_mesh_if_unused(source_mesh_without_keys)

        key_count = len(source_blocks)
        self.report(
            {"INFO"},
            f'Panda Apply Modifier: Applied "{modifier_name}" while preserving '
            f"{key_count} Shape Key{'s' if key_count != 1 else ''}.",
        )
        return {"FINISHED"}


CLASSES = (PANDA_OT_apply_modifier,)
