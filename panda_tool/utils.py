"""Pure helpers shared by Panda Tool features."""

import re


_TRAILING_NUMBER = re.compile(r"(?:_|-)\d+$")


def anchor_name(chain_root_name):
    """Build the base anchor name, removing only explicit _/- suffixes."""
    stem = _TRAILING_NUMBER.sub("", chain_root_name)
    return f"{stem}_Anchor"


def unique_name(base_name, used_names):
    """Return a Blender-style unique name without changing existing data."""
    if base_name not in used_names:
        return base_name

    index = 1
    while True:
        candidate = f"{base_name}.{index:03d}"
        if candidate not in used_names:
            return candidate
        index += 1
