# Panda Tool Blender

English | [日本語](README_JP.md)

Panda Tool is a small collection of practical Blender utilities for animation
and rigging. Version 0.7.0 adds **Remove Constraints**.

## Tools

- **Panda Apply Modifier**: apply one Modifier while preserving Shape Keys,
  including baking the current Armature pose.
- **Create Anchor**: add an anchor at each selected bone-chain root.
- **Disconnect Bones**: disable Connected for selected Edit Bones.
- **Remove Constraints**: remove all constraints from selected objects or pose bones.
- **Delete Unregistered Bones**: review and delete bones without matching vertex groups.
- **Remove Unused Vertex Groups Safe**: review and remove groups without positive weights.

## Supported Blender versions

- Blender 4.2 LTS through Blender 5.1.x
- Tested primarily on Blender 5.1 (currently Blender 5.1.1)
- Remove Constraints integration tests pass on Blender 4.2.23 LTS and 5.1.1,
  including selection isolation, animation/Driver preservation and standard
  Undo in both modes (automated background tests with Undo enabled).

Blender 3.6 is not officially supported.

## Installation

### From the Extension Repository

1. Open **Edit > Preferences > Get Extensions** in Blender.
2. Open **Repositories** and choose **Add Remote Repository**.
3. Enter the [SILL-BILL Blender Extensions repository URL](https://sill-bill.github.io/blender-extensions/index.json):

   ```text
   https://sill-bill.github.io/blender-extensions/index.json
   ```

4. Sync the repository and find **Panda Tool**.
5. Install it and enable it if necessary. If an older version is already
   installed from this repository, sync and choose **Update**.

### From a ZIP

1. Download `panda_tool-0.7.0.zip` from the
   [v0.7.0 release](https://github.com/SILL-BILL/panda-tool-blender/releases/tag/v0.7.0),
   or build it locally.
2. In Blender, open **Edit > Preferences > Get Extensions**.
3. Open the menu, choose **Install from Disk**, and select the ZIP.
4. Enable **Panda Tool** if it is not enabled automatically.

The ZIP uses the Blender Extension format introduced for Blender 4.2. Its
package root contains both `blender_manifest.toml` and `__init__.py`.

## Panda Apply Modifier

1. Select one Mesh Object in Object Mode.
2. Open **3D Viewport > Sidebar > Panda Tool > Panda Apply Modifier**.
3. Select one Modifier and click **Apply Safely**.

The tool applies the selected Modifier on disposable copies for the Basis and
every Shape Key. It verifies that all results have identical vertex, edge, and
polygon topology before replacing the original mesh. Shape Key names, order,
coordinates, values, slider ranges, mute states, vertex-group settings,
interpolation, relative-key relationships, custom properties, Actions, and
Drivers are preserved. A failure removes temporary data and leaves the original
Object unchanged. The operation supports Undo.

For an Armature Modifier, the currently evaluated pose is baked into the Basis
and every Shape Key. The Armature, its pose, animation, constraints, and the
Mesh parenting relationship are not changed. One Armature Modifier with one
valid Armature target is supported per Mesh; a confirmation dialog is shown
before applying it.

Only one Modifier and one active Mesh are processed at a time. Shape Key NLA
tracks and external references that directly target the old Shape Key datablock
are not migrated. Geometry Nodes, Boolean, Decimate, and similar
topology-dependent Modifiers are accepted only when every Shape Key produces
exactly the same topology.

## Create Anchor

1. Select an armature and enter Edit Mode.
2. Select one or more bone chains.
3. Open **3D Viewport > Sidebar > Panda Tool > Rig**.
4. Click **Create Anchor**.

For every selected chain root, Panda Tool creates an anchor whose tail meets
the root's head, makes the root a connected child, and preserves any existing
parent above the new anchor. Generated anchors are selected after the operation.
The whole operation can be reverted with one Undo.

## Disconnect Bones

1. Select an armature and enter Edit Mode.
2. Select one or more bones.
3. Open **3D Viewport > Sidebar > Panda Tool > Rig**.
4. Click **Disconnect Bones**.

The tool disables **Connected** only for the selected Edit Bones. Parent
relationships, bone transforms, animation data, constraints, and unselected
bones are left unchanged. The button is available only for an armature in Edit
Mode, and the operation can be reverted with one Undo.

## Remove Constraints

1. In Object Mode, select one or more objects; in Pose Mode, select one or
   more pose bones.
2. Open **3D Viewport > Sidebar > Panda Tool > Rig**.
3. Click **Remove Constraints**.

All constraint types on the selected targets are removed. Object Mode removes
only Object Constraints; Pose Mode removes only Bone Constraints. Unselected
targets are untouched. The target is detected automatically from the current
Blender mode. The button is disabled in other modes or without a
selection. There are no settings or confirmation dialogs.

The Info report shows the number of removed constraints and selected objects
or bones, or **No constraints found.** when there is nothing to remove.
Use **Ctrl + Z** to restore the constraints. Linked data and library overrides
are unsupported: if either occurs in the selection, the entire operation is
cancelled before changing any constraints.

The tool does not bake or compensate transforms. Stored transforms, rig
structure, parents, modifiers, Actions, animation keys, and Drivers are not
edited. Removing constraints may change the evaluated pose or appearance.
Animation or Driver paths referencing removed constraints remain unchanged
and may no longer resolve until Undo restores those constraints.

The implementation uses Object `constraints.clear()` and Blender's standard
`pose.constraints_clear()` operator for compatibility with Blender 4.2 LTS
through 5.1. Individual constraint `remove()` calls are avoided because Blender
5.1 also deletes their associated animation curves and Drivers.

## Delete Unregistered Bones

1. Make one rigged Mesh Object active in Object Mode.
2. Open **3D Viewport > Sidebar > Panda Tool > Rig**.
3. Click **Scan Unregistered Bones** and review the candidates.
4. Adjust the checkboxes, then click **Delete Checked Bones**.

Panda Tool finds the Mesh's Armature through its parent or Armature Modifier.
Bones without a same-named vertex group are candidates. Deform bones are
checked by default. Non-Deform bones are unchecked by default and marked with
a lock warning because they are commonly controllers or helper bones; the
warning does not prevent manually selecting them. **All** and **None** change
the complete candidate selection.

Candidates are checked again immediately before deletion, so a bone is kept if
a same-named vertex group was added after the scan. Children of deleted bones
are reparented to their nearest surviving ancestor. Their rest Head, Tail,
Roll, length, and direction are preserved; a reparented connected child is
disconnected when necessary to prevent Blender from snapping its Head. The
operation can be reverted with one Undo.

This tool does not rewrite bone references in Actions or FCurves, Constraint
subtargets, Drivers, or scripts. Carefully review the candidates before using
it on animated or control rigs.

## Remove Unused Vertex Groups Safe

1. Make one Mesh Object active.
2. Open **3D Viewport > Sidebar > Panda Tool > Vertex Groups**.
3. Click **Scan Unused Groups** and review the checked candidates.
4. Uncheck any groups you want to keep, then click **Remove Unused Groups**.

Only groups without a positive-weight assignment on any vertex are candidates.
A group is not considered unused merely because it has no matching armature
bone, so groups intended for Geometry Nodes, clothing, or later processing are
not removed on that basis. The selected groups are checked again immediately
before removal, the result list is refreshed afterwards, and removal can be
reverted with one Undo.

## Development tests

The Blender-independent naming tests can be run from the repository root:

```powershell
python -m unittest discover -s tests -v
```

The Blender integration tests can be run with Blender itself:

```powershell
blender --background --factory-startup --python-exit-code 1 --python tests/blender_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/remove_constraints_integration.py
```

## Build an Extension package

Run `build.bat` from the repository root, or double-click it in Explorer. The
script uses Blender's standard Extension build command and writes the package
to `dist/panda_tool-0.7.0.zip`:

```powershell
.\build.bat
```

The script uses `blender` from `PATH` first. On Windows it also checks the
standard Blender Foundation install folders, preferring Blender 5.1. For a
custom installation, set `BLENDER_EXE` before running it:

```powershell
$env:BLENDER_EXE = 'D:\Apps\Blender\blender.exe'
.\build.bat
```

Generated files under `dist/` are intentionally excluded from Git. The
same release ZIP is distributed through the SILL-BILL Blender Extensions
Repository without repacking.

## License

[GPL-3.0-only](LICENSE).

## Maintainer and repository

- Maintainer: **Gonsaku**
- Source: [SILL-BILL/panda-tool-blender](https://github.com/SILL-BILL/panda-tool-blender)
- Releases: [GitHub Releases](https://github.com/SILL-BILL/panda-tool-blender/releases)
- Extension Repository: [SILL-BILL/blender-extensions](https://github.com/SILL-BILL/blender-extensions)
