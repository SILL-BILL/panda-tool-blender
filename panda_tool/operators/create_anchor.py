"""Create an anchor bone before each selected edit-bone chain."""

from dataclasses import dataclass

import bpy

from ..utils import anchor_name, unique_name


ANCHOR_LENGTH_FACTOR = 0.5
MIN_ANCHOR_LENGTH = 0.0001


@dataclass(frozen=True)
class _AnchorPlan:
    root: object
    old_parent: object
    old_use_connect: bool
    name: str
    head: object
    tail: object
    roll: float


def _selected_chain_roots(edit_bones):
    selected = [bone for bone in edit_bones if bone.select]
    selected_names = {bone.name for bone in selected}
    roots = [
        bone
        for bone in selected
        if bone.parent is None or bone.parent.name not in selected_names
    ]
    # Armature collection order is stable, making both creation and active-bone
    # selection deterministic.
    return selected, roots


def _make_plans(edit_bones, roots):
    used_names = {bone.name for bone in edit_bones}
    plans = []

    for root in roots:
        direction = root.tail - root.head
        source_length = direction.length
        if source_length <= 0.0:
            raise ValueError(f'Bone "{root.name}" has zero length.')

        length = max(source_length * ANCHOR_LENGTH_FACTOR, MIN_ANCHOR_LENGTH)
        tail = root.head.copy()
        head = tail - direction.normalized() * length
        name = unique_name(anchor_name(root.name), used_names)
        used_names.add(name)
        plans.append(
            _AnchorPlan(
                root=root,
                old_parent=root.parent,
                old_use_connect=root.use_connect,
                name=name,
                head=head,
                tail=tail,
                roll=root.roll,
            )
        )

    return plans


class PANDA_OT_create_anchor(bpy.types.Operator):
    """Insert a non-deforming parent before each selected bone chain"""

    bl_idname = "panda_tool.create_anchor"
    bl_label = "Create Anchor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "ARMATURE" or obj.mode != "EDIT":
            self.report({"ERROR"}, "Select an armature in Edit Mode.")
            return {"CANCELLED"}

        edit_bones = obj.data.edit_bones
        selected, roots = _selected_chain_roots(edit_bones)
        if not selected:
            self.report({"WARNING"}, "No bones selected.")
            return {"CANCELLED"}

        try:
            # Validate every chain before changing the armature.
            plans = _make_plans(edit_bones, roots)
        except (ValueError, TypeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        old_active = edit_bones.active
        old_selection = {
            bone.name: (bone.select, bone.select_head, bone.select_tail)
            for bone in edit_bones
        }
        created = []

        try:
            for plan in plans:
                anchor = edit_bones.new(plan.name)
                created.append(anchor)
                anchor.head = plan.head
                anchor.tail = plan.tail
                anchor.roll = plan.roll
                anchor.use_deform = False
                anchor.parent = plan.old_parent

                plan.root.parent = anchor
                plan.root.use_connect = True

            for bone in edit_bones:
                bone.select = False
                bone.select_head = False
                bone.select_tail = False
            for anchor in created:
                anchor.select = True
                anchor.select_head = True
                anchor.select_tail = True
            edit_bones.active = created[-1]
        except Exception as exc:
            # Restore roots before removing their temporary parents.
            for plan in plans:
                plan.root.parent = plan.old_parent
                plan.root.use_connect = plan.old_use_connect
            for anchor in reversed(created):
                edit_bones.remove(anchor)
            for bone in edit_bones:
                state = old_selection.get(bone.name)
                if state is not None:
                    bone.select, bone.select_head, bone.select_tail = state
            if old_active is not None and old_active.name in edit_bones:
                edit_bones.active = edit_bones[old_active.name]
            self.report({"ERROR"}, f"Could not create anchors: {exc}")
            return {"CANCELLED"}

        count = len(created)
        self.report({"INFO"}, f"Created {count} anchor{'s' if count != 1 else ''}.")
        return {"FINISHED"}
