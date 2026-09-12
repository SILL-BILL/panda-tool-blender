import unittest

from panda_tool.utils import anchor_name, unique_name


class AnchorNameTests(unittest.TestCase):
    def test_removes_supported_numeric_suffixes(self):
        cases = {
            "Hair_01": "Hair_Anchor",
            "Hair_L_001": "Hair_L_Anchor",
            "Skirt-01": "Skirt_Anchor",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(anchor_name(source), expected)

    def test_does_not_parse_blender_dot_suffix(self):
        self.assertEqual(anchor_name("Ear.R.001"), "Ear.R.001_Anchor")

    def test_name_without_number(self):
        self.assertEqual(anchor_name("Hair"), "Hair_Anchor")


class UniqueNameTests(unittest.TestCase):
    def test_returns_base_when_available(self):
        self.assertEqual(unique_name("Hair_Anchor", set()), "Hair_Anchor")

    def test_uses_first_available_blender_suffix(self):
        used = {"Hair_Anchor", "Hair_Anchor.001", "Hair_Anchor.003"}
        self.assertEqual(unique_name("Hair_Anchor", used), "Hair_Anchor.002")


if __name__ == "__main__":
    unittest.main()
