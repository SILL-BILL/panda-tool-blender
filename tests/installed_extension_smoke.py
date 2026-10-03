"""Run regression suites against an enabled, installed Extension package."""

import importlib
import json
import runpy
import sys
import tomllib
from pathlib import Path

import addon_utils
import bpy

module_name = "bl_ext.panda_release_test.panda_tool"
package = importlib.import_module(module_name)
assert addon_utils.check(module_name)[1], "Installed extension is not enabled"
assert tomllib.loads(Path(package.__file__).with_name("blender_manifest.toml").read_text())["version"] == "0.8.0"
assert "dist" in Path(package.__file__).parts, package.__file__
assert bpy.ops.panda_tool.convert_names_to_english.get_rna_type().identifier == "PANDA_TOOL_OT_convert_names_to_english"
print("INSTALLED_EXTENSION", bpy.app.version_string, package.__file__)

# Force each unchanged integration suite to import the installed package.
# Aliases prevent source-tree modules from shadowing the Extension build.
for name, module in list(sys.modules.items()):
    if name == module_name or name.startswith(module_name + "."):
        sys.modules["panda_tool" + name[len(module_name):]] = module

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tests"))
addon_utils.disable(module_name, default_set=True)
for suite in ("blender_integration.py", "remove_constraints_integration.py",
              "convert_names_integration.py", "dictionary_second_pass_integration.py"):
    runpy.run_path(str(root / "tests" / suite), run_name="__main__")
    print("INSTALLED_SUITE_PASS", suite)
# The full Material fixture resets factory Preferences for each entry, which
# removes Extension repository namespaces. Check its dictionary tests here;
# run its native Blender fixture separately in the factory/source environment.
import unittest
from test_material_dictionary import MaterialDictionaryTests
result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(MaterialDictionaryTests))
assert result.wasSuccessful()
addon_utils.enable(module_name, default_set=True)
assert addon_utils.check(module_name)[1]
print(json.dumps({"blender": bpy.app.version_string, "version": "0.8.0",
                  "installed_path": package.__file__, "enabled": True,
                  "all_installed_suites": "PASS"}))
