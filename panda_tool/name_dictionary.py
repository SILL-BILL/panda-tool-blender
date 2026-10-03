"""Explicit aliases for Convert Names to English; no translation service.

Each category maps a standard English name to its accepted aliases. Shape
Key destinations are the supplied v0.8.0 ZZZ standard; 下眼上 uses the
user's corrected destination Eyelid_Squint.
Only full names match after NFKC normalization. Do not infer suffixes/sides.
"""

from collections import Counter
import unicodedata


NAME_ALIASES = {
    "BONE": {
        "Root": ("全ての親", "全亲", "RootBone", "全親"),
        "Center": ("センター", "中心", "CenterBone"),
        "Hips": ("下半身", "HipsBone"),
        "Chest": ("上半身", "ChestBone"),
        "Neck": ("首", "脖子", "NeckBone", "颈"),
        "Head": ("頭", "头", "HeadBone"),
        "Shoulder_L": ("左肩", "肩_L", "LeftShoulder"),
        "Shoulder_R": ("右肩", "肩_R", "RightShoulder"),
        "Arm_L": ("左腕", "左うで", "左臂", "腕_L", "LeftArm"),
        "Arm_R": ("右腕", "右うで", "右臂", "腕_R", "RightArm"),
        "Elbow_L": ("左ひじ", "左肘", "ひじ_L", "LeftElbow", "左肘部"),
        "Elbow_R": ("右ひじ", "右肘", "ひじ_R", "RightElbow", "右肘部"),
        "Wrist_L": ("左手首", "左手腕", "手首_L", "LeftWrist"),
        "Wrist_R": ("右手首", "右手腕", "手首_R", "RightWrist"),
        "Leg_L": ("左足", "左腿", "足_L", "LeftLeg"),
        "Leg_R": ("右足", "右腿", "足_R", "RightLeg"),
        "Knee_L": ("左ひざ", "左膝", "左膝盖", "ひざ_L", "LeftKnee"),
        "Knee_R": ("右ひざ", "右膝", "右膝盖", "ひざ_R", "RightKnee"),
        "Ankle_L": ("左足首", "左脚踝", "足首_L", "LeftAnkle"),
        "Ankle_R": ("右足首", "右脚踝", "足首_R", "RightAnkle"),
        "Eye_L": ("左目", "左眼", "目_L", "LeftEye"),
        "Eye_R": ("右目", "右眼", "目_R", "RightEye"),
        # MMD roles stay distinct from the existing humanoid-like names.
        "Groove": ("グルーブ", "GrooveBone"),
        "Waist": ("腰", "WaistBone"),
        "Chest2": ("上半身2", "UpperBody2"),
        "Chest3": ("上半身3", "UpperBody3"),
        "ControlCenter": ("操作中心", "ControlCenterBone"),
        "Eyes": ("両目", "双眼", "BothEyes"),
        "ArmTwist_L": ("左腕捩", "左腕捩れ", "LeftArmTwist"),
        "ArmTwist_R": ("右腕捩", "右腕捩れ", "RightArmTwist"),
        "HandTwist_L": ("左手捩", "左手捩れ", "LeftHandTwist"),
        "HandTwist_R": ("右手捩", "右手捩れ", "RightHandTwist"),
        # Preserve MMD segment numbers; do not guess anatomical segments.
        "Thumb0_L": ("左親指0", "左拇指0", "LeftThumb0"),
        "Thumb1_L": ("左親指1", "左拇指1", "LeftThumb1"),
        "Thumb2_L": ("左親指2", "左拇指2", "LeftThumb2"),
        "Thumb0_R": ("右親指0", "右拇指0", "RightThumb0"),
        "Thumb1_R": ("右親指1", "右拇指1", "RightThumb1"),
        "Thumb2_R": ("右親指2", "右拇指2", "RightThumb2"),
        "IndexFinger1_L": ("左人指1", "左人差指1", "左人差し指1", "左食指1", "LeftIndexFinger1"),
        "IndexFinger2_L": ("左人指2", "左人差指2", "左人差し指2", "左食指2", "LeftIndexFinger2"),
        "IndexFinger3_L": ("左人指3", "左人差指3", "左人差し指3", "左食指3", "LeftIndexFinger3"),
        "IndexFinger1_R": ("右人指1", "右人差指1", "右人差し指1", "右食指1", "RightIndexFinger1"),
        "IndexFinger2_R": ("右人指2", "右人差指2", "右人差し指2", "右食指2", "RightIndexFinger2"),
        "IndexFinger3_R": ("右人指3", "右人差指3", "右人差し指3", "右食指3", "RightIndexFinger3"),
        "MiddleFinger1_L": ("左中指1", "LeftMiddleFinger1"),
        "MiddleFinger2_L": ("左中指2", "LeftMiddleFinger2"),
        "MiddleFinger3_L": ("左中指3", "LeftMiddleFinger3"),
        "MiddleFinger1_R": ("右中指1", "RightMiddleFinger1"),
        "MiddleFinger2_R": ("右中指2", "RightMiddleFinger2"),
        "MiddleFinger3_R": ("右中指3", "RightMiddleFinger3"),
        "RingFinger1_L": ("左薬指1", "左无名指1", "LeftRingFinger1"),
        "RingFinger2_L": ("左薬指2", "左无名指2", "LeftRingFinger2"),
        "RingFinger3_L": ("左薬指3", "左无名指3", "LeftRingFinger3"),
        "RingFinger1_R": ("右薬指1", "右无名指1", "RightRingFinger1"),
        "RingFinger2_R": ("右薬指2", "右无名指2", "RightRingFinger2"),
        "RingFinger3_R": ("右薬指3", "右无名指3", "RightRingFinger3"),
        "LittleFinger1_L": ("左小指1", "LeftLittleFinger1"),
        "LittleFinger2_L": ("左小指2", "LeftLittleFinger2"),
        "LittleFinger3_L": ("左小指3", "LeftLittleFinger3"),
        "LittleFinger1_R": ("右小指1", "RightLittleFinger1"),
        "LittleFinger2_R": ("右小指2", "RightLittleFinger2"),
        "LittleFinger3_R": ("右小指3", "RightLittleFinger3"),
        "Toe_L": ("左つま先", "左爪先", "左脚趾", "LeftToe"),
        "Toe_R": ("右つま先", "右爪先", "右脚趾", "RightToe"),
        "LegIK_L": ("左足IK", "LeftLegIK"),
        "LegIK_R": ("右足IK", "RightLegIK"),
        "ToeIK_L": ("左つま先IK", "左爪先IK", "LeftToeIK"),
        "ToeIK_R": ("右つま先IK", "右爪先IK", "RightToeIK"),
        "LegIKParent_L": ("左足IK親", "LeftLegIKParent"),
        "LegIKParent_R": ("右足IK親", "RightLegIKParent"),
        "ShoulderParent_L": ("左肩P", "LeftShoulderParent"),
        "ShoulderParent_R": ("右肩P", "RightShoulderParent"),
        "ShoulderCancel_L": ("左肩C", "LeftShoulderCancel"),
        "ShoulderCancel_R": ("右肩C", "RightShoulderCancel"),
        "LegD_L": ("左足D", "LeftLegD"),
        "LegD_R": ("右足D", "RightLegD"),
        "KneeD_L": ("左ひざD", "左膝D", "LeftKneeD"),
        "KneeD_R": ("右ひざD", "右膝D", "RightKneeD"),
        "AnkleD_L": ("左足首D", "LeftAnkleD"),
        "AnkleD_R": ("右足首D", "RightAnkleD"),
        "WaistCancel_L": ("腰キャンセル左", "LeftWaistCancel"),
        "WaistCancel_R": ("腰キャンセル右", "RightWaistCancel"),
        "ToeEX_L": ("左足先EX", "LeftToeEX"),
        "ToeEX_R": ("右足先EX", "RightToeEX"),
    },
    "SHAPE_KEY": {
        "Eyelid_Close": ("まばたき", "眨眼", "Blink"),
        "Eyelid_Close_L": ("ウィンク２", "左眨眼", "BlinkLeft"),
        "Eyelid_Close_R": ("ウィンク２右", "右眨眼", "BlinkRight"),
        "Eyelid_Smile": ("笑い", "笑眼", "EyeSmile"),
        "Eyelid_Smile_L": ("ウィンク", "左笑眼", "EyeSmileLeft"),
        "Eyelid_Smile_R": ("ウィンク右", "右笑眼", "EyeSmileRight"),
        "Eyelid_Surprise": ("びっくり", "惊讶", "EyeSurprise"),
        "Eyelid_Surprise_R": ("びっくり右", "右惊讶", "EyeSurpriseRight"),
        "Eyelid_Surprise_L": ("びっくり左", "左惊讶", "EyeSurpriseLeft"),
        "Eyelid_Jito": ("じと目", "死鱼眼", "JitoEye"),
        "Eyelid_Serious": ("怒り目２", "严肃眼", "SeriousEye"),
        "Eyelid_Angry": ("怒り目", "愤怒眼", "AngryEye"),
        "Eyelid_Sad": ("悲しむ", "悲伤眼", "SadEye"),
        "EyeOuterCorner_Down": ("眼角下", "OuterEyeCornerDown"),
        "Eyelid_Squint": ("下眼上", "LowerEyelidUp"),
        "A": ("あ",),
        "I": ("い",),
        "U": ("う",),
        "E": ("え",),
        "O": ("お",),
        "Wa": ("ワ",),
        "Mouth_Shout": ("□",),
        "I2": ("い２",),
        "O2": ("お２",),
        "E2": ("え２",),
        "Wa2": ("ワ２",),
        "Mouth_Triangle": ("▲",),
        "Mouth_Smirk": ("にやり",),
        "MouthRight": ("口右",),
        "MouthLeft": ("口左",),
        "MouthUp": ("口上",),
        "MouthDown": ("口下",),
        "Mouth_Spread": ("口横広げ",),
        "Mouth_Narrow": ("口横狭め",),
        "Mouth_CornerDown": ("口角下げ",),
        "Mouth_CornerUp": ("口角上げ",),
        "Mouth_Spread_R": ("口横広げ右",),
        "Mouth_Spread_L": ("口横広げ左",),
        "Mouth_Narrow_L": ("口横狭め左",),
        "Mouth_Narrow_R": ("口横狭め右",),
        "Mouth_CornerDown_R": ("口角下げ右",),
        "Mouth_CornerDown_L": ("口角下げ左",),
        "Mouth_CornerUp_R": ("口角上げ右",),
        "Mouth_CornerUp_L": ("口角上げ左",),
        "Brow_Serious": ("真面目",),
        "Brow_Sad": ("困る",),
        "Brow_Angry": ("怒り",),
        "Brow_Smile": ("にこり",),
        "Brow_Up_L": ("上左",),
        "Brow_Up_R": ("上右",),
        "Brow_Up": ("上",),
        "Brow_Down": ("下",),
    },
    "MATERIAL": {
        "Skin": ("肌", "皮膚", "皮肤", "肤色", "skin"),
        "Hair": ("髪", "髪の毛", "头发", "hair", "髮"),
        "Face": ("顔", "面部", "face", "颜", "頭脸"),
        "EyeWhite": ("白目", "eyeWhite"),
        "Eye": ("眼睛", "eye", "目"),
        "Eyebrow": ("眉毛", "eyebrow"),
        "Mouth": ("口", "嘴", "mouth", "口腔"),
        "Clothes": ("服", "衣服", "clothes"),
        "Shoes": ("靴", "鞋子", "shoes"),
        "Eyelash": ("まつ毛", "睫毛", "eyelash", "睫"),
        "Teeth": ("歯", "牙齿", "teeth", "牙", "齿"),
        "Tongue": ("舌", "舌头", "tongue"),
        "HairFront": ("前髪", "刘海", "FrontHair"),
        "HairBack": ("後髪", "後ろ髪", "后发", "BackHair"),
        "Underwear": ("肌着", "内衣", "underwear"),
        "Accessory": ("アクセサリ", "アクセサリー", "饰品", "accessory"),
        # User-supplied Material standard; these exact destinations take
        # precedence over the earlier 眼白 / 眉 / 瞳 aliases.
        "Sclera": ("眼白",),
        "OralCavity": ("口舌",),
        "EyelidCrease": ("二重",),
        "Brow": ("眉",),
        "Eyelash+": ("睫+",),
        "Eye_HL": ("目光", "瞳-高光"),
        "Iris": ("瞳",),
        "Hair+": ("髮+",),
        "Body": ("体",),
        "Eye_Shadow": ("目影",),
        "Top": ("上衣",),
        "Sleeve": ("袖",),
        "MouthLine": ("口线",),
        "Neck": ("首",),
        "Glass": ("镜片",),
    },
    "OBJECT": {
        "Body": ("体", "身体", "body"),
        "Face": ("顔", "面部", "face"),
        "Eyes": ("目", "眼睛", "eyes"),
        "Head": ("頭", "头", "head"),
        "Hair": ("髪", "髪の毛", "头发", "hair"),
        "Clothes": ("服", "衣服", "clothes"),
        "Shoes": ("靴", "鞋子", "shoes"),
        "Armature": ("骨格", "骨架", "armature"),
        "HairFront": ("前髪", "刘海", "FrontHair"),
        "HairBack": ("後髪", "後ろ髪", "后发", "BackHair"),
        "Eyebrow": ("眉", "眉毛", "eyebrow"),
        "Eyelash": ("まつ毛", "睫毛", "eyelash"),
        "Mouth": ("口", "嘴", "mouth"),
        "Teeth": ("歯", "牙齿", "teeth"),
        "Tongue": ("舌", "舌头", "tongue"),
        "Accessory": ("アクセサリ", "アクセサリー", "饰品", "accessory"),
    },
}


def _build_lookup(aliases):
    lookup = {}
    for english_name, names in aliases.items():
        for name in (english_name, *names):
            normalized = unicodedata.normalize("NFKC", name)
            if normalized in lookup and lookup[normalized] != english_name:
                raise ValueError(f"Ambiguous name alias: {name!r}")
            lookup[normalized] = english_name
    return lookup


NAME_LOOKUPS = {category: _build_lookup(aliases)
                for category, aliases in NAME_ALIASES.items()}


def english_name(category, name):
    """Return a known standard name, or None without modifying the input."""
    return NAME_LOOKUPS[category].get(unicodedata.normalize("NFKC", name))


def plan_names(category, names, occupied_names=None):
    """Plan exact renames; skip occupied names and all duplicate destinations.

    Occupancy uses actual Blender names, not normalized names. Names occupied
    at the start remain reserved even if another rename would vacate them.
    Returns (renames, collisions, unknown_count, unchanged_count).
    """
    names = list(names)
    occupied = set(names if occupied_names is None else occupied_names)
    candidates = []
    unknown_count = unchanged_count = 0
    for name in names:
        destination = english_name(category, name)
        if destination is None:
            unknown_count += 1
        elif destination == name:
            unchanged_count += 1
        else:
            candidates.append((name, destination))
    counts = Counter(destination for _, destination in candidates)
    renames, collisions = [], []
    for source, destination in candidates:
        if destination in occupied or counts[destination] > 1:
            collisions.append((source, destination))
        else:
            renames.append((source, destination))
    return renames, collisions, unknown_count, unchanged_count
