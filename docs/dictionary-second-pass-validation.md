# Panda Tool v0.8.0 辞書第二次強化・検証結果

この報告は辞書第二次強化時点の履歴です。最新のMaterial対応と検証結果は[Material辞書追加報告](material-dictionary-update-validation.md)を参照してください。

検証日: 2026-10-03。未リリース候補。commit・tag・GitHub Release・Extension Repository公開は行っていない。

実装前の資料比較と採否は[辞書比較レポート](dictionary-second-pass-comparison.md)に記録した。
既存の照合・Rename・Undo・Rollback・UIは維持した。参照再検証で発見したBlender固有の配列要素Driverパスについてのみ、安全な事前CANCEL検査を追加した。Driverのパスを独自に書き換える処理は追加していない。

## Previous / New Dictionary Counts

| カテゴリ | Previous | New | Entries Added |
|---|---:|---:|---:|
| Bone | 22 | 84 | 62 |
| Shape Key | 52 | 52 | 0 |
| Material | 9 | 16 | 7 |
| Object | 8 | 16 | 8 |

件数は標準英語名の数。Alias件数（標準名自身を除く、NFKC重複除去前）はBone 253、Shape Key 80、Material 54、Object 51。Shape Keyは標準52項目だけでなく既存Aliasも実装前Fixtureとの完全一致を確認した。既存の全標準名・全Aliasの変換先を維持。

## Bone Entries Added

単独6件: Groove、Waist、Chest2、Chest3、ControlCenter、Eyes。

以下は各_L／_Rの左右2件ずつ（28種類 × 2 = 56件）。

| 種類 | 新規標準名（末尾に_L／_R） |
|---|---|
| Twist | ArmTwist、HandTwist |
| Thumb | Thumb0、Thumb1、Thumb2 |
| Index | IndexFinger1、IndexFinger2、IndexFinger3 |
| Middle | MiddleFinger1、MiddleFinger2、MiddleFinger3 |
| Ring | RingFinger1、RingFinger2、RingFinger3 |
| Little | LittleFinger1、LittleFinger2、LittleFinger3 |
| Toe | Toe |
| IK | LegIK、ToeIK、LegIKParent |
| Shoulder | ShoulderParent、ShoulderCancel |
| D | LegD、KneeD、AnkleD |
| Other | WaistCancel、ToeEX |

指番号はMMDの番号を保持。指名や番号を実行時に分割・推測する処理はなく、個々の完全名を辞書へ列挙した。

## Material / Object Entries Added

- Material 7件: Eyelash、Teeth、Tongue、HairFront、HairBack、Underwear、Accessory。
- Object 8件: HairFront、HairBack、Eyebrow、Eyelash、Mouth、Teeth、Tongue、Accessory。
- 既存EntryへのAlias追加: 全親 → Root、颈 → Neck、左右肘部 → Elbow_L/R、眼白 → EyeWhite、Materialの目 → Eye。既存Aliasを削除・変更していない。

## Rejected / Ambiguous Entries

番号なしの左右指、親指3、他指0/4、指先、左右なしの肩P/C・D系、グループ、番号付き捩補助、汎用の補助／調整／ダミー／胸、パンツ／飾りは不採用・保留。役割・Segment・意味が曖昧なため。髪影、髪2、前髪_透明、左足IK.001なども未知の完全名として保持。詳しい採否は比較レポートを参照。

Shape Key追加候補は今回採用しない。正式52項目の追加・削除・改名は0件。

## Japanese Alias / Simplified Chinese / English Alias Tests

すべてPASS。全カテゴリの全登録Aliasについて、NFKC後の期待英語名、既存英語名との衝突Skip、変換後の再実行0件を確認した。追加標準名は独立した期待値一覧と照合した。

日本語には人指／人差指／人差し指、つま先／爪先、捩／捩れ、全親を含む。簡体字には颈、拇指・食指・无名指の番号付き左右名、双眼、脚趾、睫毛、牙齿、舌头、刘海、后发、内衣、饰品等を含む。英語にはLeftArmTwist、RightShoulderCancel、FrontHair等を含む。中指・小指の表記は日本語と中国語で共通。

Blenderに依存しないテストは13件PASS（既存ユーティリティテスト含む）。

## Bone Reference Preservation

Blender 4.2.23 LTS／5.1.1ともPASS。追加Bone全62件を持つテストリグで、各Boneの同名Vertex Group、Pose Bone、Bone Parent、Constraint subtarget、TRANSFORMS Driverのbone_target、SINGLE_PROP DriverのScalarプロパティ参照、Animation F-Curveパスを確認した。Bone階層・設定・ウェイト・Armature Modifier参照を保持。全新規Material 7件／Object 8件も同じOperatorで実変換した。

全保存データの比較とフレーム1／10の評価済みGeometry比較により、通常処理と強制失敗後RollbackでRig挙動を保持したことを確認した。Undo後も全62件の名前・参照・Geometry復元を確認。

### Driverに関する安全上の制限

両バージョンで、BlenderネイティブのBone RenameがSINGLE_PROPの配列要素パス（例: `pose.bones["左腕捩"].rotation_euler[0]`）を更新しないケースを確認した。Rename対象Boneにこの形式のDriver参照がある場合、Operatorは名称変更前に操作全体をCANCELする。独自のDriver書き換えはしない。この事前CANCELと全データ不変も両バージョンでPASS。

したがって、配列要素Driverを持つ全リグでRenameが完了するという保証はしない。ScalarプロパティとTRANSFORMS参照は全62件で更新・復元を確認した。

## Collision / Undo / Second Run / Rollback

| 検証 | 4.2.23 LTS | 5.1.1 |
|---|---|---|
| 全Aliasの衝突Skip・新規名前生成なし | PASS | PASS |
| 同一変換先を要求する複数AliasのSkip | PASS | PASS |
| 未選択Object／Materialが占有する変換先のSkip | PASS | PASS |
| BoneのVertex Group名衝突Skip | PASS | PASS |
| Blender標準Undo | PASS | PASS |
| Second Runの変換0件 | PASS | PASS |
| 全カテゴリ変換後の強制失敗Rollback | PASS | PASS |
| Basis／改名済みReference Key保持 | PASS | PASS |
| Linked Data CANCEL | PASS | PASS |
| Library Override CANCEL | PASS | PASS |
| 不安全なBone配列要素Driverの事前CANCEL | PASS | PASS |

全Aliasの衝突と再実行は共通Pythonテスト、Bone／Shape Key／Material／Objectの実衝突・Undo・RollbackはBlender統合テストで確認。

## Yanagi Before / After

| 対象 | Before | After (4.2 / 5.1) | 増加 |
|---|---:|---:|---:|
| Bone | 22 | 27 | +5 |
| Shape Key | 52 | 52 | 0 |
| Material | 2 | 3 | +1 |
| Object | 0 | 0 | 0 |

今回追加で変換されたBone: グルーブ → Groove、腰 → Waist、上半身2 → Chest2、両目 → Eyes、操作中心 → ControlCenter。
Material: 目 → Eye（既存標準名への新しいAlias）。衝突は0件。未登録の複合Object名は変更されず0件。

Yanagi通常検証と、検証コピーのメモリ上にDriver／Animationを補った検証の両方を両バージョンで実施。原本のShape Key Driverは0件のため、元からDriverを持つ実モデルを検証したとは扱わない。追加テストでは1件のShape Key Driverと外部Driver変数・Mouth Animationを保持した。

Geometry・UV・Weight・Bone階層／Pose設定・Modifier・Constraint・Material Slot／Node／設定・Shape Key値／設定・Custom Property・Action／F-Curve／Driverを前後比較した。フレーム0／10の評価済みGeometry、Undo、再実行もPASS。Workbench 512×512の前後画像は各バージョン内で全画素一致。画像間の版をまたぐ一致は要件としていない。

原本 `D:\3dmodel\3dmodel-zzz\x03-Yanagi\Yanagi-001\Yanagi.org.blend` は上書きしていない。検証コピーとJSON、画像、ログはRepository内の`dist/`へ保存した。原本のSHA256と更新日時を前後比較して不変を確認。

原本SHA256: `c0669cf8a17a3edf8b68a953f2f4e34f3c8fb2cea2a6ef0253c9d87e495f513c`。

### Blender 4.2.23 LTSの制限

Blender 5形式の原本を4.2で直接開けないため、前回作成した4.5.9経由の互換コピー `dist/Yanagi.blender42_test_source.blend` を使用した。4.2読み込み時には新しい版のデータと旧Render Engine識別子の警告が出る。検証は互換コピー内でのRename前後比較であり、5.1から4.2への全設定の無損失変換を保証しない。Workbench比較時は検証用Camera・Workbenchを一時設定した。

## Blender Versions / Regression Tests

- Blender 4.2.23 LTS: 既存3統合スイート、新規第二次辞書統合スイート、Yanagi通常／Driver付き検証、Workbench前後比較すべてPASS。
- Blender 5.1.1: 同じ検証すべてPASS。
- 既存Create Anchor／Disconnect Bones／Delete Unregistered Bones／Remove Unused Vertex Groups／Panda Apply Modifier／Remove Constraintsの回帰スイートを再実行してPASS。
- 5.1のLinked Dataテストでは一時ファイル書き込みのsandbox制限が発生したため、許可済み環境で再実行してPASS。実装不具合として扱わない。
- `git diff --check` PASS。CRLF変換のGit警告のみ。
- 未公開のローカルExtension ZIPを再ビルドし、Blender標準Extension validate PASS。

## README Status / git status

README.mdとREADME_JP.mdを更新済み。辞書件数・MMD番号と役割・不採用名・比較レポート・配列要素DriverのCANCEL制限・テストコマンドを記載。

既存v0.8.0候補の未コミット変更を維持している。HEADは既存v0.7.0の`57de9df`。変更はすべて未ステージ。今回のcommit・tag・push・Release・Extension Repository更新は0件。

```text
 M README.md
 M README_JP.md
 M build.bat
 M panda_tool/__init__.py
 M panda_tool/blender_manifest.toml
 M panda_tool/operators/__init__.py
 M panda_tool/ui/panels.py
?? docs/
?? panda_tool/name_dictionary.py
?? panda_tool/operators/convert_names_to_english.py
?? tests/convert_names_integration.py
?? tests/convert_names_real_model.py
?? tests/dictionary_second_pass_integration.py
?? tests/fixtures/
?? tests/name_conversion_checks.py
?? tests/render_name_conversion.py
?? tests/test_name_dictionary.py
```

`dist/`の検証コピー・JSON・PNG・ログ・ZIPはGit管理対象外。結果確認までここで停止する。
