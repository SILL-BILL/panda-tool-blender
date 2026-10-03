import json
from pathlib import Path
import unicodedata
import unittest

from panda_tool.name_dictionary import NAME_ALIASES, english_name, plan_names

FIXTURES = Path(__file__).parent / "fixtures"
MATERIAL_MAPPING = json.loads((FIXTURES / "material_dictionary_update.json").read_text(encoding="utf-8"))
APPROVED_CHANGES = {"眼白": "Sclera", "眉": "Brow", "瞳": "Iris"}


class MaterialDictionaryTests(unittest.TestCase):
    def test_full_official_mapping(self):
        self.assertEqual(len(MATERIAL_MAPPING), 26)
        for source, destination in MATERIAL_MAPPING.items():
            with self.subTest(source=source):
                self.assertEqual(english_name("MATERIAL", source), destination)
                self.assertEqual(plan_names("MATERIAL", [source])[0], [(source, destination)])
                self.assertEqual(plan_names("MATERIAL", [destination])[0], [])
                self.assertEqual(plan_names("MATERIAL", [source, destination])[1], [(source, destination)])
        self.assertEqual(plan_names("MATERIAL", ["髮", "髮+"])[0],
                         [("髮", "Hair"), ("髮+", "Hair+")])

    def test_compatibility_except_explicit_overrides(self):
        baseline = json.loads((FIXTURES / "name_dictionary_v080_second_pass.json").read_text(encoding="utf-8"))
        for category, entries in baseline.items():
            if category != "MATERIAL":
                self.assertEqual(NAME_ALIASES[category], {d: tuple(a) for d, a in entries.items()})
            for destination, aliases in entries.items():
                for source in (destination, *aliases):
                    expected = APPROVED_CHANGES.get(source, destination) if category == "MATERIAL" else destination
                    self.assertEqual(english_name(category, source), expected)
        self.assertEqual(len(NAME_ALIASES["MATERIAL"]), 31)
        all_aliases = [unicodedata.normalize("NFKC", source)
                       for aliases in NAME_ALIASES["MATERIAL"].values() for source in aliases]
        self.assertEqual(len(all_aliases), len(set(all_aliases)))

    def test_unknowns_keep_original_spelling(self):
        # 内衣 is an existing alias and remains supported; do not add the
        # other unspecified clothing names or their numbered variants.
        unknowns = ["衣服01", "衣服02", "裙子", "未知材质", "CustomMaterial",
                    "目影01", "目影_透明", "目影2", "髮++.001", "裙", "裤", "鞋",
                    "袜", "外套", "装饰", "ＣｕｓｔｏｍＭａｔｅｒｉａｌ", " 颜", "颜 "]
        self.assertEqual(plan_names("MATERIAL", unknowns), ([], [], len(unknowns), 0))
        self.assertEqual(english_name("MATERIAL", "内衣"), "Underwear")
        self.assertEqual(english_name("MATERIAL", "睫＋"), "Eyelash+")

    def test_aliases_competing_for_destination_skip(self):
        for sources, destination in ((["颜", "頭脸"], "Face"), (["牙", "齿"], "Teeth"),
                                     (["目光", "瞳-高光"], "Eye_HL")):
            self.assertEqual(plan_names("MATERIAL", sources)[:2],
                             ([], [(source, destination) for source in sources]))


if __name__ == "__main__":
    unittest.main()
