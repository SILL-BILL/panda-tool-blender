# Panda Tool Blender

Panda Tool is a small collection of practical Blender utilities for animation
and rigging. Version 0.5.0 adds **Panda Apply Modifier** to the existing rigging
and cleanup tools.

## Supported Blender versions

- Blender 4.2 LTS through Blender 5.1
- Tested primarily on Blender 5.1 (currently Blender 5.1.1)

Blender 3.6 is not officially supported.

## Installation

1. Download or build `panda_tool-0.5.0.zip`.
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

Only one Modifier and one active Mesh are processed at a time. Armature
Modifiers are intentionally rejected in version 0.5.0. NLA tracks on the Shape
Key datablock and external references that directly target the old Shape Key
datablock are not migrated. Geometry Nodes, Boolean, Decimate, and similar
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
blender --background --python tests/blender_integration.py
```

## Build an Extension package

Run `build.bat` from the repository root, or double-click it in Explorer. The
script uses Blender's standard Extension build command and writes the package
to `dist/panda_tool-0.5.0.zip`:

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
resulting ZIP can later be published as part of a self-hosted Blender Extension
Repository.
