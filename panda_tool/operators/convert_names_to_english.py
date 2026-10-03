"""Convert known model names using only the bundled dictionary."""

import bpy

from ..name_dictionary import plan_names


def conversion_targets(context):
    """Selected objects plus armatures referenced by parents/modifiers."""
    objects = list(context.selected_objects)
    seen = {obj.as_pointer() for obj in objects}
    for obj in list(objects):
        related = []
        parent = obj.parent
        while parent is not None:
            if parent.type == "ARMATURE":
                related.append(parent)
            parent = parent.parent
        related.extend(modifier.object for modifier in obj.modifiers
                       if modifier.type == "ARMATURE" and modifier.object)
        for armature in related:
            if armature.as_pointer() not in seen:
                objects.append(armature)
                seen.add(armature.as_pointer())
    return objects


def _unique(values):
    return list({value.as_pointer(): value for value in values}.values())


def _editable(data):
    return data.is_editable and data.library is None and data.override_library is None


def conversion_plan(context):
    """Validate all owners and plan every category before changing any data.

    Native name setters maintain Blender's references. Vertex Groups are not
    independently translated; their destinations must remain safe when Blender
    follows a bone rename. Shared data are processed once, without copying.
    """
    objects = conversion_targets(context)
    armatures = _unique(obj.data for obj in objects if obj.type == "ARMATURE")
    keys = _unique(obj.data.shape_keys for obj in objects
                   if obj.type == "MESH" and obj.data.shape_keys)
    materials = _unique(slot.material for obj in objects for slot in obj.material_slots
                        if slot.material)
    owners = _unique([*objects, *armatures, *keys, *materials])
    for owner in owners:
        if not _editable(owner):
            raise ValueError(f"Linked data or Library Override is unsupported: '{owner.name}'.")
    for obj in objects:
        if obj.type == "ARMATURE" and obj.mode != "OBJECT":
            raise ValueError("All target armatures must be in Object Mode.")

    plan = []
    conflicts = 0

    def add(category, targets, occupied):
        nonlocal conflicts
        by_name = {target.name: target for target in targets}
        renames, collisions, _, _ = plan_names(category, by_name, occupied)
        conflicts += len(collisions)
        for source, destination in renames:
            plan.append((category, by_name[source], source, destination))

    for armature in armatures:
        add("BONE", list(armature.bones), armature.bones.keys())
    # Check native bone rename's secondary effects before making any changes.
    safe_plan = []
    for category, bone, source, destination in plan:
        related = [obj for obj in bpy.data.objects
                   if obj.data == bone.id_data or
                   (obj.parent and obj.parent.data == bone.id_data) or
                   any(modifier.type == "ARMATURE" and modifier.object and
                       modifier.object.data == bone.id_data for modifier in obj.modifiers)]
        for obj in related:
            if not _editable(obj) or (obj.data and not _editable(obj.data)):
                raise ValueError(f"Bone references use linked/override data: '{obj.name}'.")
        if any(obj.vertex_groups.get(destination) is not None for obj in related):
            conflicts += 1
            continue
        safe_plan.append((category, bone, source, destination))
    plan = safe_plan

    for key in keys:
        # Exclude the reference key by identity, even if Basis was renamed.
        targets = [block for block in key.key_blocks
                   if block != key.reference_key and block.name != "Basis"]
        add("SHAPE_KEY", targets, key.key_blocks.keys())
    add("MATERIAL", materials, bpy.data.materials.keys())
    add("OBJECT", objects, bpy.data.objects.keys())

    # Blender 4.2/5.1 may leave SINGLE_PROP driver paths to array elements
    # unchanged on native bone rename. Cancel rather than write Driver data
    # ourselves or leave a path that would break on reload.
    bone_prefixes = {}
    for category, bone, source, _ in plan:
        if category != "BONE":
            continue
        escaped = bpy.utils.escape_identifier(source)
        bone_prefixes.setdefault(bone.id_data, []).append(f'bones["{escaped}"]')
        for rig in bpy.data.objects:
            if rig.type == "ARMATURE" and rig.data == bone.id_data:
                bone_prefixes.setdefault(rig, []).append(f'pose.bones["{escaped}"]')
    if bone_prefixes:
        driver_owners = set(bone_prefixes)
        for users in bpy.data.user_map(subset=set(bone_prefixes)).values():
            driver_owners.update(users)
        for owner in driver_owners:
            animation = getattr(owner, "animation_data", None)
            if not animation:
                continue
            for curve in animation.drivers:
                for variable in curve.driver.variables:
                    if variable.type != "SINGLE_PROP":
                        continue
                    for target in variable.targets:
                        path = target.data_path
                        prefixes = bone_prefixes.get(target.id, ())
                        array_index = path.rsplit("[", 1)[-1]
                        if (path.startswith(tuple(prefix + "." for prefix in prefixes))
                                and array_index.endswith("]") and array_index[:-1].isdigit()):
                            raise ValueError(
                                f"Bone array Driver path cannot be safely renamed: '{path}'.")

    # Native renames may update animation references. Reject non-editable
    # animation owners rather than modifying them through Blender's setters.
    if plan:
        for users in bpy.data.user_map(subset=set(owners)).values():
            if any(not _editable(user) for user in users):
                raise ValueError("Target data are referenced by linked data or Library Overrides.")
        for data in owners:
            animation = getattr(data, "animation_data", None)
            if animation:
                actions = [animation.action] if animation.action else []
                actions.extend(strip.action for track in animation.nla_tracks
                               for strip in track.strips if strip.action)
                if any(not _editable(action) for action in actions):
                    raise ValueError(f"Animation uses linked/override data: '{data.name}'.")
    return plan, conflicts


class PANDA_OT_convert_names_to_english(bpy.types.Operator):
    """Convert known names on selected objects and their model data"""

    bl_idname = "panda_tool.convert_names_to_english"
    bl_label = "Convert Names to English"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT":
            cls.poll_message_set("Use Object Mode.")
            return False
        if not context.selected_objects:
            cls.poll_message_set("Select at least one model object.")
            return False
        return True

    def execute(self, context):
        if context.mode != "OBJECT" or not context.selected_objects:
            self.report({"WARNING"}, "Select model objects in Object Mode.")
            return {"CANCELLED"}
        try:
            plan, conflicts = conversion_plan(context)
        except ValueError as exc:
            self.report({"WARNING"}, str(exc))
            return {"CANCELLED"}

        applied = []
        counts = dict.fromkeys(("BONE", "SHAPE_KEY", "MATERIAL", "OBJECT"), 0)
        try:
            for category, target, source, destination in plan:
                target.name = destination
                applied.append((target, source))
                if target.name != destination:
                    raise RuntimeError(f"Could not rename '{source}' exactly to '{destination}'.")
                counts[category] += 1
        except Exception as exc:
            # Reverse native renames as a transaction; reverse order restores
            # references and avoids introducing suffixes while rolling back.
            for target, source in reversed(applied):
                target.name = source
            self.report({"WARNING"}, f"Conversion cancelled; names restored: {exc}")
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Converted: {sum(counts.values())}. Bones: {counts['BONE']}; "
            f"Shape Keys: {counts['SHAPE_KEY']}; Materials: {counts['MATERIAL']}; "
            f"Objects: {counts['OBJECT']}; Conflicts: {conflicts}.",
        )
        return {"FINISHED"}
