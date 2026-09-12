# Panda Tool Blender

Panda Tool is a small collection of practical Blender utilities for animation
and rigging. Version 0.3.0 contains **Create Anchor**, **Disconnect Bones**, and
**Remove Unused Vertex Groups Safe**.

## Supported Blender versions

- Blender 4.2 LTS through Blender 5.1
- Tested primarily on Blender 5.1 (currently Blender 5.1.1)

Blender 3.6 is not officially supported.

## Installation

1. Download or build `panda_tool-0.3.0.zip`.
2. In Blender, open **Edit > Preferences > Get Extensions**.
3. Open the menu, choose **Install from Disk**, and select the ZIP.
4. Enable **Panda Tool** if it is not enabled automatically.

The ZIP uses the Blender Extension format introduced for Blender 4.2. Its
package root contains both `blender_manifest.toml` and `__init__.py`.

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
to `dist/panda_tool-0.3.0.zip`:

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
