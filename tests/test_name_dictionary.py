import json
from pathlib import Path
import unittest
import unicodedata

from panda_tool.name_dictionary import NAME_ALIASES, english_name, plan_names


# Independent expected mappings from the reviewed second-pass specification.
SECOND_PASS_ENTRIES = {
    "BONE": {
        "グルーブ": "Groove", "腰": "Waist", "上半身2": "Chest2",
        "上半身3": "Chest3", "操作中心": "ControlCenter", "両目": "Eyes",
    },
    "MATERIAL": {
        "まつ毛": "Eyelash", "歯": "Teeth", "舌": "Tongue",
        "前髪": "HairFront", "後髪": "HairBack", "肌着": "Underwear",
        "アクセサリ": "Accessory",
    },
    "OBJECT": {
        "前髪": "HairFront", "後髪": "HairBack", "眉": "Eyebrow",
        "まつ毛": "Eyelash", "口": "Mouth", "歯": "Teeth",
        "舌": "Tongue", "アクセサリ": "Accessory",
    },
}
for side, suffix in (("左", "_L"), ("右", "_R")):
    for source, destination in (
        ("腕捩", "ArmTwist"), ("手捩", "HandTwist"), ("つま先", "Toe"),
        ("足IK", "LegIK"), ("つま先IK", "ToeIK"), ("足IK親", "LegIKParent"),
        ("肩P", "ShoulderParent"), ("肩C", "ShoulderCancel"),
        ("足D", "LegD"), ("ひざD", "KneeD"), ("足首D", "AnkleD"),
        ("足先EX", "ToeEX"),
    ):
        SECOND_PASS_ENTRIES["BONE"][side + source] = destination + suffix
    SECOND_PASS_ENTRIES["BONE"]["腰キャンセル" + side] = "WaistCancel" + suffix
    for finger, destination, numbers in (
        ("親指", "Thumb", (0, 1, 2)),
        ("人指", "IndexFinger", (1, 2, 3)),
        ("中指", "MiddleFinger", (1, 2, 3)),
        ("薬指", "RingFinger", (1, 2, 3)),
        ("小指", "LittleFinger", (1, 2, 3)),
    ):
        for number in numbers:
            SECOND_PASS_ENTRIES["BONE"][side + finger + str(number)] = destination + str(number) + suffix


class NameDictionaryTests(unittest.TestCase):
    def test_second_pass_expected_entries_and_counts(self):
        self.assertEqual({c: len(d) for c, d in NAME_ALIASES.items()},
                         {"BONE": 84, "SHAPE_KEY": 52, "MATERIAL": 31, "OBJECT": 16})
        baseline = json.loads((Path(__file__).parent / "fixtures" /
                               "name_dictionary_v080_first_pass.json").read_text(encoding="utf-8"))
        self.assertEqual(NAME_ALIASES["SHAPE_KEY"],
                         {name: tuple(aliases) for name, aliases in baseline["SHAPE_KEY"].items()})
        for category, entries in baseline.items():
            for destination, aliases in entries.items():
                for source in (destination, *aliases):
                    approved = {"眉": "Brow", "瞳": "Iris"} if category == "MATERIAL" else {}
                    self.assertEqual(english_name(category, source), approved.get(source, destination))
        for category, expected in SECOND_PASS_ENTRIES.items():
            added = set(NAME_ALIASES[category]) - set(baseline[category])
            expected_added = set(expected.values())
            if category == "MATERIAL":
                official = json.loads((Path(__file__).parent / "fixtures" /
                                       "material_dictionary_update.json").read_text(encoding="utf-8"))
                expected_added.update(set(official.values()) - set(baseline[category]))
            self.assertEqual(added, expected_added)
            for source, destination in expected.items():
                self.assertEqual(english_name(category, source), destination)

    def test_all_aliases_collision_and_second_run(self):
        for category, entries in NAME_ALIASES.items():
            for destination, aliases in entries.items():
                for source in aliases:
                    with self.subTest(category=category, source=source):
                        self.assertEqual(english_name(category, source), destination)
                        normalized = unicodedata.normalize("NFKC", source)
                        self.assertEqual(english_name(category, normalized), destination)
                        if source != destination:
                            self.assertEqual(plan_names(category, [source])[0], [(source, destination)])
                            self.assertEqual(plan_names(category, [source, destination])[0], [])
                            self.assertEqual(plan_names(category, [source, destination])[1], [(source, destination)])
                        self.assertEqual(plan_names(category, [destination])[0], [])

    def test_second_pass_language_and_role_distinctions(self):
        for source, destination in (
            ("全親", "Root"), ("颈", "Neck"), ("左膝", "Knee_L"),
            ("左食指２", "IndexFinger2_L"), ("右无名指３", "RingFinger3_R"),
            ("左拇指０", "Thumb0_L"), ("右小指１", "LittleFinger1_R"),
            ("左爪先ＩＫ", "ToeIK_L"), ("右足ＩＫ親", "LegIKParent_R"),
            ("LeftArmTwist", "ArmTwist_L"), ("RightShoulderCancel", "ShoulderCancel_R"),
        ):
            self.assertEqual(english_name("BONE", source), destination)
        for category in ("MATERIAL", "OBJECT"):
            self.assertEqual(english_name(category, "睫毛"), "Eyelash")
            self.assertEqual(english_name(category, "FrontHair"), "HairFront")
        self.assertEqual(english_name("MATERIAL", "内衣"), "Underwear")
        for source in ("左親指", "右人差指", "左親指3", "左人指0", "肩P", "足D",
                       "グループ", "左腕捩1", "左足IK.001", "左食指4"):
            self.assertIsNone(english_name("BONE", source))
        for category in ("MATERIAL", "OBJECT"):
            for source in ("髪影", "髪2", "前髪_透明", "パンツ", "CustomAccessory"):
                self.assertIsNone(english_name(category, source))

    def test_shape_key_standard_is_exact(self):
        expected = {
            "まばたき": "Eyelid_Close", "ウィンク２": "Eyelid_Close_L",
            "ウィンク２右": "Eyelid_Close_R", "笑い": "Eyelid_Smile",
            "ウィンク": "Eyelid_Smile_L", "ウィンク右": "Eyelid_Smile_R",
            "びっくり": "Eyelid_Surprise", "びっくり右": "Eyelid_Surprise_R",
            "びっくり左": "Eyelid_Surprise_L", "じと目": "Eyelid_Jito",
            "怒り目２": "Eyelid_Serious", "怒り目": "Eyelid_Angry",
            "悲しむ": "Eyelid_Sad", "眼角下": "EyeOuterCorner_Down",
            "下眼上": "Eyelid_Squint",
            "あ": "A", "い": "I", "う": "U", "え": "E", "お": "O",
            "ワ": "Wa", "□": "Mouth_Shout", "い２": "I2", "お２": "O2",
            "え２": "E2", "ワ２": "Wa2", "▲": "Mouth_Triangle",
            "にやり": "Mouth_Smirk", "口右": "MouthRight", "口左": "MouthLeft",
            "口上": "MouthUp", "口下": "MouthDown", "口横広げ": "Mouth_Spread",
            "口横狭め": "Mouth_Narrow", "口角下げ": "Mouth_CornerDown",
            "口角上げ": "Mouth_CornerUp", "口横広げ右": "Mouth_Spread_R",
            "口横広げ左": "Mouth_Spread_L", "口横狭め左": "Mouth_Narrow_L",
            "口横狭め右": "Mouth_Narrow_R", "口角下げ右": "Mouth_CornerDown_R",
            "口角下げ左": "Mouth_CornerDown_L", "口角上げ右": "Mouth_CornerUp_R",
            "口角上げ左": "Mouth_CornerUp_L", "真面目": "Brow_Serious",
            "困る": "Brow_Sad", "怒り": "Brow_Angry", "にこり": "Brow_Smile",
            "上左": "Brow_Up_L", "上右": "Brow_Up_R", "上": "Brow_Up", "下": "Brow_Down",
        }
        for source, destination in expected.items():
            with self.subTest(source=source):
                self.assertEqual(english_name("SHAPE_KEY", source), destination)

    def test_aliases_and_nfkc(self):
        for source in ("左腕", "左うで", "左臂", "LeftArm", "ＬｅｆｔＡｒｍ"):
            self.assertEqual(english_name("BONE", source), "Arm_L")
        self.assertEqual(english_name("SHAPE_KEY", "ウィンク2"), "Eyelid_Close_L")
        self.assertEqual(english_name("SHAPE_KEY", "ｳｨﾝｸ２"), "Eyelid_Close_L")
        self.assertEqual(english_name("SHAPE_KEY", "眨眼"), "Eyelid_Close")
        self.assertEqual(english_name("MATERIAL", "皮肤"), "Skin")
        self.assertEqual(english_name("OBJECT", "身体"), "Body")

    def test_unknown_names_are_not_inferred(self):
        names = ["熊猫超级披风骨骼01", "謎ボーン", "CustomAccessory",
                 "左腕.001", " 左腕", "左腕 ", "左腕01", "ｃｕｓｔｏｍ"]
        renames, collisions, unknown, unchanged = plan_names("BONE", names)
        self.assertEqual((renames, collisions, unknown, unchanged), ([], [], len(names), 0))

    def test_existing_target_and_alias_conflicts_skip(self):
        renames, collisions, unknown, unchanged = plan_names(
            "BONE", ["左腕", "Arm_L", "右腕", "RightArm", "首"],
        )
        self.assertEqual(renames, [("首", "Neck")])
        self.assertEqual(collisions, [("左腕", "Arm_L"), ("右腕", "Arm_R"), ("RightArm", "Arm_R")])
        self.assertEqual((unknown, unchanged), (0, 1))

    def test_unselected_global_occupancy_and_idempotence(self):
        self.assertEqual(plan_names("OBJECT", ["体"], ["体", "Body"])[0], [])
        self.assertEqual(plan_names("SHAPE_KEY", ["Eyelid_Squint"])[0], [])
        self.assertEqual(plan_names("SHAPE_KEY", ["まばたき", "Eyelid_Close"])[1],
                         [("まばたき", "Eyelid_Close")])


if __name__ == "__main__":
    unittest.main()
