# Panda Tools Blender

## Project Overview

Panda Tools Blender is a collection of small Blender utilities intended to improve practical 3DCG animation workflows.

The project prioritizes simple, reliable tools over large monolithic systems.

## Development Principles

- Keep each tool as independent as reasonably possible.
- Prefer simple implementations over unnecessary abstraction.
- Do not perform large refactors unless they are required.
- Do not modify unrelated tools when implementing a feature.
- Preserve existing behavior unless a change is explicitly requested.
- Use Blender's official Python API whenever possible.

## Naming

- Use English for internal names, classes, operators, properties, modules, and files.
- Prefer clear descriptive names over abbreviations.
- User-facing Japanese text may be used where appropriate.

## Blender Support

Primary development environment:

- Blender 5.1

Compatibility with older Blender versions may be considered later.

Do not introduce version-specific behavior without documenting it.

## UI

Panda Tools should use a consistent Blender UI location.

When adding a new feature:

- Keep the UI compact.
- Avoid unnecessary options.
- Prefer sensible defaults.
- Do not clutter the N-panel.

## Safety

Tools that modify rigs, bones, meshes, animation data, or other user data should avoid destructive operations where possible.

Before destructive processing:

- Validate required objects and modes.
- Validate selections.
- Fail safely with a useful error message.

## Documentation

When adding or changing a user-facing feature:

- Update the README when appropriate.
- Document important limitations.
- Document Blender version requirements if relevant.

## Current Tool Philosophy

Panda Tools is a practical toolbox for animation production.

A tool should ideally solve one specific recurring production problem well.