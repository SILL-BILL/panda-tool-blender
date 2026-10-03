# Panda Tool v0.8.0 Material辞書追加・再検証結果

検証日: 2026-10-03。ユーザー指定の正式26項目を追加した未リリース候補。
commit・tag・GitHub Release・Extension Repository公開は行っていない。

## Dictionary Counts / Entries

| 項目 | 結果 |
|---|---|
| Previous Material Dictionary Count | 16 |
| New Material Dictionary Count | 31 |
| New Entries Added | 標準英語名15件、既存未登録の入力Alias20件 |
| Existing Entries Reused | 入力・出力とも同じ3件（白目 → EyeWhite、目 → Eye、肌 → Skin） |
| Existing Entries Changed | 入力Aliasの変換先3件（下表） |
| Bone / Shape Key / Object | 84 / 52 / 16件、全Entry・全Alias不変 |

登録数は標準英語名の数。Materialの入力Aliasは54→74件（標準英語名自身を除く）。
正式26項目の内訳は、新しい入力20件＋既存入力の変換先変更3件＋既存対応の再利用3件。
同じ変換先にはAliasを追加し、辞書Entryや同じ入力を重複登録していない。

追加した標準英語名15件:

```text
Sclera
OralCavity
EyelidCrease
Brow
Eyelash+
Eye_HL
Iris
Hair+
Body
Eye_Shadow
Top
Sleeve
MouthLine
Neck
Glass
```

正式表で既存標準名を利用する変換先は8種類（Face、Teeth、EyeWhite、Mouth、Eyelash、Eye、Hair、Skin）。
正式表全26項目の期待値は[テストFixture](../tests/fixtures/material_dictionary_update.json)にそのまま記録した。

### Existing Entries Changed: Previous / New / Reason

| 入力 | Previous | New | Reason |
|---|---|---|---|
| 眼白 | EyeWhite | Sclera | 今回のユーザー指定正式表を優先 |
| 眉 | Eyebrow | Brow | 今回のユーザー指定正式表を優先 |
| 瞳 | Eye | Iris | 今回のユーザー指定正式表を優先 |

旧標準名EyeWhite・Eyebrow・Eyeは削除していない。白目 → EyeWhite、眉毛／eyebrow → Eyebrow、眼睛／eye／目 → Eyeなど、変更指定されていないAliasを維持。

今回の服飾名追加は上衣 → Top、袖 → Sleeveのみ。指定外の衣装名は調査・推測して追加していない。
内衣 → Underwear等の**既存**衣装Aliasは、既存辞書維持の指示に従って保持した。

## Full Material Mapping / Unknown / Conflict / Undo / Second Run

| 検証 | 4.2.23 LTS | 5.1.1 |
|---|---|---|
| Full Material Mapping Test（正式26項目） | PASS | PASS |
| Unknown Material Test | PASS | PASS |
| Conflict Test（既存・未割当Materialの名前を含む） | PASS | PASS |
| Undo Test（Blender標準Undo） | PASS | PASS |
| Second Run Test（追加変更0件） | PASS | PASS |

純Pythonテスト17件PASS。正式表全26項目について独立したFixtureと完全一致を確認し、全旧Aliasの後方互換を正式変更3件の例外のみ許可して検証した。
Bone・Shape Key・Objectは実装前辞書Fixtureとの完全一致を確認。

Blender統合テストでは26項目を1件ずつ実際にOperatorへ渡して、Rename・設定保持・再実行・Undo・衝突Skipを検証した。
Face／Teeth／Eye_HLのように複数入力が同じ出力を要求する場合は、全対象Skipする既存仕様も確認した。
髮 → Hair、髮+ → Hair+を区別し、睫＋のNFKC照合も確認した。

未知名として衣服01、衣服02、裙子、未知材质、CustomMaterial、目影01、目影_透明、目影2、未指定衣装名を保持。
全角の未知名ＣｕｓｔｏｍＭａｔｅｒｉａｌも元の表記を保持し、正規化した未知名へRenameしていない。

## Material Data Preservation

| 検証 | 結果・根拠 |
|---|---|
| Material Slot Preservation | PASS。Materialの同一ID、重複Slot、Slot順序、未選択の共有利用先を維持 |
| Shader Preservation | PASS。Nodeの種類・設定・Socket値・Node Link・Surface設定・Viewport Colorを前後比較 |
| Texture Preservation | PASS。Image／TextureのID・設定・参照、Image Pixelの内容を比較 |
| Driver Preservation | PASS。Material roughnessのDriverを正式26項目の各Fixtureで維持 |
| Animation Preservation | PASS。Material diffuse_colorのAction／F-Curveを維持し、フレーム1／10で値を確認 |
| Custom Property Preservation | PASS。Material Custom Propertyの値を維持 |
| Geometry Preservation | PASS。Geometry・UV・Weightの完全比較と評価済みGeometry比較 |

製品のOperator・照合・衝突・Undo・Rollback・Linked／Override検査・Bone Driver安全検査は今回変更していない。
製品コードの今回の変更対象はMaterial辞書のみ。
検証コードにはImage／Textureの独立したスナップショットと、ネストしたCustom Propertyの再帰比較を追加した。
Image Pixelはチェックサムで比較し、巨大なPixel配列をJSONへ展開しない。

## Yanagi Previous / New Material Converted

| 項目 | 辞書第二次強化後 | 今回（4.2 / 5.1） |
|---|---:|---:|
| Material Converted | 3 | 15 |
| Bone Converted | 27 | 27 |
| Shape Key Converted | 52 | 52 |
| Object Converted | 0 | 0 |
| Conflicts | 0 | 0 |

Materialは+12件。今回の実モデル変換15件:

```text
颜 → Face
口线 → MouthLine
白目 → EyeWhite
二重 → EyelidCrease
目光 → Eye_HL
目 → Eye
口舌 → OralCavity
齿 → Teeth
目影 → Eye_Shadow
体 → Body
首 → Neck
肌 → Skin
髮 → Hair
髮+ → Hair+
镜片 → Glass
```

Yanagi通常検証と、検証コピーのメモリ上にShape Key Driver・外部Driver変数・Mouth Animationを補った検証の両方でPASS。
原本のShape Key Driverは0件のため、Driver付き検証はコピーに補ったデータとして区別している。
Geometry・UV・Weight・Material Slot順序・Shader Node／Link・Image／Texture・Driver／Animation・Custom Propertyを比較。
フレーム0／10の評価済みGeometry、標準Undo、再実行0件も確認した。

### Workbench Comparison

両バージョンで512×512画像のRename前後が全画素一致（PASS）。

- 4.2.23 LTS: `6d613efc4c1819770733418069329e426fe0cdf4d381830411fff6de153fe68c`
- 5.1.1: `9d8132f4cef455a2a570ceabfd6ea965813b577ad9dd39addd529aa4aacedc8d`

値は各バージョン内の前後Pixel内容のチェックサム。版をまたぐ描画一致ではない。
原本のScene／Render設定は保存せず、検証プロセス内だけでWorkbenchとCameraを設定した。

## Blender Versions / Original Yanagi Modified

- Blender 4.2.23 LTS: 全テストPASS。既存の4.5.9経由の互換コピーを使用。
- Blender 5.1.1: 全テストPASS。原本を読み込み、保存先はRepository内の検証コピーだけ。
- Original Yanagi Modified: **NO**。原本のSHA256と更新日時の前後一致を確認。

原本: `D:\3dmodel\3dmodel-zzz\x03-Yanagi\Yanagi-001\Yanagi.org.blend`

SHA256: `c0669cf8a17a3edf8b68a953f2f4e34f3c8fb2cea2a6ef0253c9d87e495f513c`

4.2はBlender 5形式の原本を直接開けないため、`dist/Yanagi.blender42_test_source.blend`でRename前後を検証した。
新しい版のデータと旧Render Engine識別子の読み込み警告が出る。
これは5.1から4.2への全設定の無損失互換性を保証する検証ではない。

## Regression Tests

両バージョンで既存3スイートと第二次辞書スイートを再実行してPASS。

- Create Anchor
- Disconnect Bones
- Remove Unused Vertex Groups Safe
- Safe Unregistered Bone Cleanup
- Panda Apply Modifier
- Remove Constraints

Bone 84、Shape Key 52、Object 16、全日本語／簡体字／英語Alias、未知名保持、Conflict Skip、Undo、Second Run、途中失敗Rollback、Linked Data CANCEL、Library Override CANCEL、Bone Driver安全CANCELもPASS。
骨名の配列要素Driverパスがある場合の事前CANCELは、前回と同じ条件を維持している。

### 検証中に解消した問題

Image比較の初期追加時、Imageメタデータ取得が初回にBufferを初期化し、検証の最初のスナップショットだけが異なる失敗が出た。
再現条件はImage／Textureカテゴリを追加した直後の最初の比較。影響範囲は検証コード。
メタデータ取得後の安定した状態とPixelチェックサムを記録するよう修正し、該当統合・Yanagi通常／Driver付き検証を両版で再実行してPASS。製品のRename処理を変更して解消したものではない。

5.1のLinked Data用一時ファイルは既存のsandbox制限を避ける許可済み環境で検証した。
未解決の実装・テスト失敗はない。4.2のファイル互換性とBone配列要素Driverの事前CANCELという既存の制限は残る。

## README.md / README_JP.md / Package

README.md: 更新済み。Material 31件、完全一致、日本語／中国語Alias、未知衣装名保持、指定変更3件と服飾追加の限定を記載。
README_JP.md: 同等内容を更新済み。

未公開のローカルZIPを再ビルドし、Blender標準Extension validate PASS。
`dist/panda_tool-0.8.0.zip`（22,384 bytes）
SHA256: `3de09af1283fe9d7b0fc8563977f14ff33725ca05e70fa1a6eef0e6db21be141`

検証コピー、JSON、画像、ログ、ZIPはGit管理対象外の`dist/`へ保存。

## git status

HEADは既存v0.7.0の`57de9df`。前回までのv0.8.0候補の変更を保持し、すべて未ステージ・未コミット。

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
?? tests/material_dictionary_integration.py
?? tests/name_conversion_checks.py
?? tests/render_name_conversion.py
?? tests/test_material_dictionary.py
?? tests/test_name_dictionary.py
```

`git diff --check` PASS（GitのCRLF変換警告のみ）。commit・tag・push・Release・Extension Repository公開は0件。結果確認まで停止する。
