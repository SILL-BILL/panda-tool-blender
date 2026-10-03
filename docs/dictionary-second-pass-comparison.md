# v0.8.0 辞書第二次強化・実装前比較

調査日: 2026-10-03。実装前の採否を記録する。外部辞書・CSV・コードは取り込まず、名称の存在と役割を確認する参考資料として閲覧した。頻度の統計調査ではなく、標準・準標準の名称と複数実装での使用確認である。

## 資料と方式の比較

[MMD Toolsの翻訳モジュール](https://github.com/MMD-Blender/blender_mmd_tools/blob/main/mmd_tools/translations.py)では、指名・捩・グルーブ・操作中心や、肘／ひじ、人指／人差指の表記を確認した。同モジュールには部分文字列を置換する処理がある。Panda Toolはその方式を採用せず、NFKC後の完全一致を維持する。既存のRoot・Hips・Chestを別の命名方式へ変更しない。

[Hogarthの翻訳CSV](https://github.com/Hogarth-MMD/mmd_tools_translation/blob/master/translations.csv)は指・衣服などの語彙の存在確認に使用した。単語表から複合名を生成して翻訳することはしない。

[nanoemの準標準ボーン仕様](https://github.com/hkrn/nanoem/blob/main/docs/plugin.rst)で捩、IK親、肩P/C、D系、腰キャンセル、足先EX、操作中心の役割を確認した。P/C・D・EXは通常Boneと区別する。操作中心はRootとは別の視点中心用Boneとして扱う。

[Bone Tools作者のMMDプリセット](https://github.com/namakoshiro/blender-bone-tools/blob/main/presets.json)と[モーションプラグイン作者の名称一覧](https://www.lemorin.jp/other/ey_recordingmotion.html)で親指0/1/2、他4指1/2/3、左右の表記を確認した。Humanoid関節名への割当は実装によって異なるため、Panda Toolでは原番号を保持する。

## 現在登録済み

標準英語名の数: Bone 22、Shape Key 52、Material 9、Object 8。Alias数やNFKCによる表記数とは区別する。

- Bone: Root、Center、Hips、Chest、Neck、Head。左右それぞれShoulder、Arm、Elbow、Wrist、Leg、Knee、Ankle、Eye。既存英語名・Aliasを全て維持する。
- Material: Skin、Hair、Face、EyeWhite、Eye、Eyebrow、Mouth、Clothes、Shoes。
- Object: Body、Face、Eyes、Head、Hair、Clothes、Shoes、Armature。
- Shape Key: 正式52項目と既存Aliasを固定。下眼上 → Eyelid_Squintも維持。

## 追加候補と追加採用

候補を意味・番号・左右が明確なものに絞り、次を採用する。左右行は_Lと_Rの2件。表の番号範囲は辞書に列挙する個別Entryであり、実行時の文字列分割や推測ルールではない。

| 分類 | 日本語候補 | 採用する標準英語名 | 理由 |
|---|---|---|---|
| Body | グルーブ、腰、上半身2、上半身3 | Groove、Waist、Chest2、Chest3 | 既存Chestと番号付き上半身を区別 |
| Control / Eyes | 操作中心、両目 | ControlCenter、Eyes | Rootや片目とは別の役割 |
| Twist 左右 | 腕捩、手捩 | ArmTwist、HandTwist | 通常Arm/Wristに統合しない |
| Fingers 左右 | 親指0/1/2 | Thumb0、Thumb1、Thumb2 | 親指0を省略しない |
| Fingers 左右 | 人指／人差指／人差し指1/2/3 | IndexFinger1/2/3 | 同義表記を番号別に対応 |
| Fingers 左右 | 中指1/2/3、薬指1/2/3、小指1/2/3 | MiddleFinger1/2/3、RingFinger1/2/3、LittleFinger1/2/3 | 原番号を保持 |
| Toe 左右 | つま先／爪先 | Toe | IKと区別 |
| IK 左右 | 足IK、つま先IK、足IK親 | LegIK、ToeIK、LegIKParent | IK固有の役割を保持 |
| Shoulder 左右 | 肩P、肩C | ShoulderParent、ShoulderCancel | 親と回転キャンセルの役割を区別 |
| D 左右 | 足D、ひざD／膝D、足首D | LegD、KneeD、AnkleD | 回転補正系列を通常脚と区別 |
| Other 左右 | 腰キャンセル左／右、左／右足先EX | WaistCancel、ToeEX | 通常腰・つま先から区別 |
| Material | まつ毛、歯、舌、前髪、後髪、肌着、アクセサリ | Eyelash、Teeth、Tongue、HairFront、HairBack、Underwear、Accessory | 自由名の分割をせず完全な部位名のみ |
| Object | 前髪、後髪、眉、まつ毛、口、歯、舌、アクセサリ | HairFront、HairBack、Eyebrow、Eyelash、Mouth、Teeth、Tongue、Accessory | 単純部位名のみ |

Bone新規62件、Material新規7件、Object新規8件を予定。合計は84 / 52 / 16 / 16。

既存Entryにも同義Aliasを追加する。全親 → Root、颈 → Neck、左右膝・肘の簡体字表記など。Materialの目は既存Eyeへ、Objectの目は既存Eyesへ対応し、既存瞳 → Eyeを変えない。簡体字は意味が明確な部位（拇指、食指、中指、无名指、小指、脚趾、睫毛、牙齿、舌头、刘海、后发、内衣、饰品等）と番号付き完全名に限定する。MMD補助Boneに推測した中国語名は付けない。英語AliasもLeft/Rightと役割が明示された完全名のみ登録する。

## 曖昧なので不採用・今回保留

| 候補 | 判断 |
|---|---|
| 左親指、右親指、左人差指など番号なしの指 | どのSegmentか不明。番号付きBoneへ統合しない |
| 親指3、他指0/4、指先 | 標準番号との同一視を避け、今回の範囲外として保留 |
| 肩P、肩C、足Dなど左右なしの補助名 | 左右を推測しない。左右の完全名のみ採用 |
| グループ | Grooveの誤字と決めつけない。Groupの別意味がある |
| 左腕捩1等の補助番号、補助、調整、ダミー、胸 | この追加パスでは役割・作者独自番号を十分確定できないため保留 |
| パンツ、飾り | 衣類の意味や装飾の範囲が揺れるため自動対応しない |
| 髪影、髪2、前髪_透明、左足IK.001 | 登録済み語を含んでも未知の完全名として保持 |

Shape Keyの追加採用・変更は0件。今回は新規Morph候補も採用しない。

## 実装・検証方針

既存Operator・UI・照合・衝突・Undo・Rollback処理を変更しない。実装前辞書をテストFixtureへ保存して後方互換とShape Key全Alias不変を確認する。全追加Aliasの期待結果、衝突、二度目実行を自動検証する。追加Bone全件についてBlenderネイティブRename後の参照、Undo、Rollbackを検証し、既存テストとYanagi再検証・Workbench比較を4.2.23 LTS／5.1.1で行う。4.2では既存互換コピーを使用する。commit・tag・Release・公開は行わない。

実装後追記: 参照テストでBlenderの配列要素Driverパスが更新されないケースを検出したため、このケースだけ事前CANCELの安全検査を追加した。採用辞書・標準名・Rename方式の変更はない。[検証結果](dictionary-second-pass-validation.md)に再現条件と結果を記録した。
