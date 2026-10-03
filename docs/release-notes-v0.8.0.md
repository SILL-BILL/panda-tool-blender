## What's New

### Convert Names to English

Added **Convert Names to English** under **Panda Tool > Rig** to convert known
model names to standardized English names.

Supported data:

- Bones
- Shape Keys
- Materials
- Objects

Features:

- Japanese names, Simplified Chinese aliases and known English aliases.
- Exact-match dictionary conversion after Unicode NFKC normalization.
- Unknown names retain their original spelling.
- Destination-name conflicts are skipped without generating numbered names.
- Standard Blender Undo and safe re-execution.
- Rollback on unexpected write failure.
- Linked Data and Library Overrides cancel the operation before modification.

Current built-in dictionary:

- 84 Bone mappings
- 52 Shape Key mappings
- 31 Material mappings
- 16 Object mappings

The 52 ZZZ Shape Key mappings remain fixed, including
`下眼上` → `Eyelid_Squint`. Approved Material destinations include
`眼白` → `Sclera`, `眉` → `Brow` and `瞳` → `Iris`.

## Safety

Native Blender name setters retain dependent references. The tool preserves
animation, Drivers, constraints, modifiers, geometry, UVs, weights, Material
settings, transforms and hierarchy. Shared datablocks remain shared; their
renames and dependent reference updates can affect unselected users.

Potentially unsafe Bone Driver reference patterns are detected before renaming
and the entire operation is safely cancelled. This includes SINGLE_PROP paths
to Bone array elements that Blender does not safely update on native rename.
Custom Property values, script strings and external mappings are not translated.

## Documentation

Updated the English and Japanese READMEs with matching specifications,
dictionary behavior, safety limits and Extension Repository installation steps.

## Compatibility

Tested with:

- Blender 4.2.23 LTS
- Blender 5.1.1

Yanagi validation converted 27 Bones, 52 Shape Keys and 15 Materials, with
0 Object conversions and no conflicts. Geometry, UVs, weights and references
were preserved, and Workbench before/after pixels were identical.
The original validation file was not modified.

The Blender 4.2 Yanagi validation used a compatibility copy saved through
Blender 4.5 LTS because the original was saved in Blender 5 format.

Existing-tool regression tests passed for Create Anchor, Disconnect Bones,
Remove Unused Vertex Groups Safe, Safe Unregistered Bone Cleanup,
Panda Apply Modifier and Remove Constraints.

## Installation

Download **panda_tool-0.8.0.zip** and use **Install from Disk**, or sync the
[SILL-BILL Blender Extensions repository](https://sill-bill.github.io/blender-extensions/index.json)
and install/update **Panda Tool**.
