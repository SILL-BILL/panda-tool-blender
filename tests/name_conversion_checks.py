"""Preservation checks shared by fixture and real-model name conversion tests."""

import hashlib
import json
from array import array

import bpy


def identifier(value):
    return value.as_pointer() if value is not None else None


def custom_value(value):
    if isinstance(value, bpy.types.ID):
        return identifier(value)
    if isinstance(value, dict):
        return {key: custom_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [custom_value(item) for item in value]
    if hasattr(value, "to_dict"):
        return {key: custom_value(item) for key, item in value.items()}
    if hasattr(value, "to_list"):
        return [custom_value(item) for item in value.to_list()]
    return value


def properties(value, inverse=None):
    """Record scalar RNA settings and pointers, excluding runtime metadata."""
    inverse = inverse or {}
    result = {}
    for prop in value.bl_rna.properties:
        name = prop.identifier
        if name in {"rna_type", "name", "is_valid", "is_updated", "is_updated_data",
                    "is_updated_transform", "select", "select_head", "select_tail", "pixels"}:
            continue
        if prop.type == "COLLECTION":
            continue
        try:
            item = getattr(value, name)
            if prop.type == "POINTER":
                item = identifier(item)
            elif prop.is_array:
                item = list(item)
            elif isinstance(item, str):
                item = normalize_name(item, inverse)
            elif isinstance(item, set):
                item = sorted(item)
            result[name] = item
        except (AttributeError, TypeError, ValueError):
            continue
    return result


def normalize_name(value, inverse):
    if value in inverse:
        return inverse[value]
    for new, old in inverse.items():
        value = value.replace('[' + json.dumps(new) + ']', '[' + json.dumps(old, ensure_ascii=False) + ']')
    return value


def action_curves(action):
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    return [curve for layer in action.layers for strip in layer.strips
            for bag in strip.channelbags for curve in bag.fcurves]


def curve_snapshot(curve, inverse):
    return {
        "settings": properties(curve, inverse),
        "points": [properties(point) for point in curve.keyframe_points],
        "samples": [properties(point) for point in curve.sampled_points],
        "modifiers": [properties(modifier) for modifier in curve.modifiers],
    }


def animation_snapshot(data, inverse):
    animation = data.animation_data
    if not animation:
        return None
    return {
        "settings": properties(animation),
        "drivers": [{"curve": curve_snapshot(curve, inverse),
                     "driver": properties(curve.driver),
                     "variables": [(properties(var), [properties(target, inverse)
                                     for target in var.targets]) for var in curve.driver.variables]}
                    for curve in animation.drivers],
        "nla": [(track.name, properties(track),
                 [(strip.name, properties(strip), [curve_snapshot(f, inverse)
                                                   for f in strip.fcurves])
                  for strip in track.strips]) for track in animation.nla_tracks],
    }


def geometry_snapshot(mesh):
    return {
        "vertices": [(tuple(v.co), [(g.group, g.weight) for g in v.groups]) for v in mesh.vertices],
        "edges": [tuple(e.vertices) for e in mesh.edges],
        "polygons": [(tuple(p.vertices), p.material_index, p.use_smooth) for p in mesh.polygons],
        "uv": [(layer.name, [tuple(value.uv) for value in layer.data]) for layer in mesh.uv_layers],
    }


def stored_snapshot(inverse=None, details=False):
    """Digest names separately; allow only native reference path/name updates."""
    inverse = inverse or {}
    result = {"objects": {}, "meshes": {}, "armatures": {}, "keys": {}, "materials": {},
              "actions": {}, "images": {}, "textures": {}}
    for obj in bpy.data.objects:
        entry = {
            "settings": properties(obj, inverse),
            "name": normalize_name(obj.name, inverse),
            "collections": [identifier(c) for c in obj.users_collection],
            "modifiers": [(m.name, properties(m, inverse)) for m in obj.modifiers],
            "constraints": [(c.name, properties(c, inverse)) for c in obj.constraints],
            "slots": [(slot.link, identifier(slot.material)) for slot in obj.material_slots],
            "groups": [(normalize_name(g.name, inverse), g.index, g.lock_weight) for g in obj.vertex_groups],
            "custom": {name: custom_value(obj[name]) for name in obj.keys()},
            "animation": animation_snapshot(obj, inverse),
        }
        if obj.pose:
            entry["pose"] = [(normalize_name(b.name, inverse), properties(b, inverse),
                              [(c.name, properties(c, inverse)) for c in b.constraints])
                             for b in obj.pose.bones]
        result["objects"][identifier(obj)] = entry
    for mesh in bpy.data.meshes:
        result["meshes"][identifier(mesh)] = geometry_snapshot(mesh)
    for armature in bpy.data.armatures:
        result["armatures"][identifier(armature)] = [
            (normalize_name(b.name, inverse), properties(b, inverse)) for b in armature.bones]
    for key in bpy.data.shape_keys:
        result["keys"][identifier(key)] = {
            "settings": properties(key), "animation": animation_snapshot(key, inverse),
            "blocks": [(normalize_name(b.name, inverse), properties(b, inverse),
                        [tuple(p.co) for p in b.data]) for b in key.key_blocks],
        }
    for material in bpy.data.materials:
        tree = material.node_tree
        result["materials"][identifier(material)] = {
            "name": normalize_name(material.name, inverse),
            "settings": properties(material, inverse), "animation": animation_snapshot(material, inverse),
            "custom": {name: custom_value(material[name]) for name in material.keys()},
            "node_animation": animation_snapshot(tree, inverse) if tree else None,
            "nodes": [(n.name, properties(n), [properties(s) for s in n.inputs],
                       [properties(s) for s in n.outputs]) for n in tree.nodes] if tree else None,
            "links": [(identifier(link.from_node), link.from_socket.identifier,
                       identifier(link.to_node), link.to_socket.identifier) for link in tree.links] if tree else None,
        }
    for action in bpy.data.actions:
        result["actions"][identifier(action)] = {
            "name": action.name,
            "curves": [curve_snapshot(curve, inverse) for curve in action_curves(action)],
        }
    for image in bpy.data.images:
        # Reading Image metadata can initialize its buffer. Read settings
        # first, then capture the resulting stable buffer state without
        # putting millions of pixel values into the JSON settings snapshot.
        properties(image)
        pixels = None
        if image.has_data:
            values = array("f", [0]) * len(image.pixels)
            image.pixels.foreach_get(values)
            pixels = hashlib.sha256(values.tobytes()).hexdigest()
        result["images"][identifier(image)] = {
            "name": image.name, "settings": properties(image), "pixels": pixels,
            "custom": {name: custom_value(image[name]) for name in image.keys()},
        }
    for texture in bpy.data.textures:
        result["textures"][identifier(texture)] = {
            "name": texture.name, "settings": properties(texture),
            "animation": animation_snapshot(texture, inverse),
            "custom": {name: custom_value(texture[name]) for name in texture.keys()},
        }
    # JSON ordering is stable within each collection; floating-point geometry
    # and UV/weight data remain exact rather than using a loose tolerance.
    if details:
        return result
    return {category: hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()
            for category, values in result.items()}


def differences(before, after, path=""):
    if isinstance(before, dict) and isinstance(after, dict):
        for key in before.keys() | after.keys():
            if key not in before or key not in after:
                yield path + "/" + str(key), "missing"
            else:
                yield from differences(before[key], after[key], path + "/" + str(key))
    elif isinstance(before, (list, tuple)) and isinstance(after, (list, tuple)):
        if len(before) != len(after):
            yield path, (len(before), len(after))
        else:
            for index, (a, b) in enumerate(zip(before, after)):
                yield from differences(a, b, path + "/" + str(index))
    elif before != after:
        yield path, (before, after)


def evaluated_geometry():
    graph = bpy.context.evaluated_depsgraph_get()
    result = {}
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            evaluated = obj.evaluated_get(graph)
            mesh = evaluated.to_mesh()
            try:
                result[identifier(obj)] = [tuple(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices]
            finally:
                evaluated.to_mesh_clear()
    return result


def assert_geometry_close(before, after):
    assert before.keys() == after.keys()
    for key in before:
        assert len(before[key]) == len(after[key])
        assert all(abs(a - b) < 1e-6 for vertex_a, vertex_b in zip(before[key], after[key])
                   for a, b in zip(vertex_a, vertex_b)), key
