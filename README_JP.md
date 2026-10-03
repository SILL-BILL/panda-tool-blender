# Panda Tool Blender

[English](README.md) | 日本語

Panda Toolは、Blenderでのアニメーション制作やリギングを効率化する、
小さな実用ツールのコレクションです。v0.8.0で **Convert Names to English** を追加しました。

## 機能一覧

- **Panda Apply Modifier**：Shape Keysを保持してModifierを1つ適用します。現在のArmatureのポーズのベイクにも対応します。
- **Create Anchor**：選択したBoneチェーンのルートにAnchorを追加します。
- **Disconnect Bones**：選択したEdit BoneのConnectedを解除します。
- **Remove Constraints**：選択したObjectまたはPose BoneのConstraintをすべて削除します。
- **Convert Names to English**：内蔵辞書で既知のBone・Shape Key・Material・Object名を英語へ変換します。
- **Delete Unregistered Bones**：対応するVertex GroupがないBoneを確認して削除します。
- **Remove Unused Vertex Groups Safe**：正のウェイトがないVertex Groupを確認して削除します。

## 対応Blender Version

- Blender 4.2 LTS ～ Blender 5.1.x
- 主な検証環境はBlender 5.1（現在はBlender 5.1.1）です。
- Remove Constraintsの統合テストはBlender 4.2.23 LTS／5.1.1で成功しています。
  両モードでの選択範囲の保護、アニメーション・Driverの保持、標準Undoを確認しています
  （Undoを有効にしたバックグラウンドでの自動テスト）。

Blender 3.6は正式サポートの対象外です。

## インストール

### Extension Repositoryから

1. Blenderで **Edit > Preferences > Get Extensions** を開きます。
2. **Repositories** から **Add Remote Repository** を選びます。
3. [SILL-BILL Blender ExtensionsのRepository URL](https://sill-bill.github.io/blender-extensions/index.json)を入力します。

   ```text
   https://sill-bill.github.io/blender-extensions/index.json
   ```

4. Repositoryを同期し、**Panda Tool** を探します。
5. インストールし、必要に応じて有効にします。このRepositoryから旧バージョンを
   インストール済みの場合は、同期後に **Update** を選んで更新します。

### ZIPから

1. [v0.8.0のRelease](https://github.com/SILL-BILL/panda-tool-blender/releases/tag/v0.8.0)から
   `panda_tool-0.8.0.zip`をダウンロードするか、ローカルでビルドします。
2. Blenderで **Edit > Preferences > Get Extensions** を開きます。
3. メニューから **Install from Disk** を選び、ZIPを指定します。
4. 自動で有効にならない場合は **Panda Tool** を有効にします。

ZIPはBlender 4.2で導入されたExtension形式です。
パッケージのルートに`blender_manifest.toml`と`__init__.py`が含まれています。

## Panda Apply Modifier

1. Object ModeでMesh Objectを1つ選択します。
2. **3D Viewport > Sidebar > Panda Tool > Panda Apply Modifier** を開きます。
3. Modifierを1つ選び、**Apply Safely** をクリックします。

BasisとすべてのShape Keyについて、一時的なコピーに選択したModifierを適用します。
各結果の頂点・辺・ポリゴンのトポロジーが完全に一致することを確認してから、元のMeshを置き換えます。
Shape Keyの名前、順序、座標、値、スライダー範囲、Mute、Vertex Group設定、補間、
Relative Keyの参照関係、カスタムプロパティ、Action、Driverを保持します。
失敗した場合は一時データを削除し、元のObjectを変更せずに終了します。Undoに対応しています。

Armature Modifierでは、現在評価されているポーズをBasisとすべてのShape Keyにベイクします。
Armature本体、ポーズ、アニメーション、Constraint、MeshのParent関係は変更しません。
Meshごとに、有効なArmatureを参照するArmature Modifierを1つだけ処理できます。
適用前には確認ダイアログを表示します。

処理対象は1回につきアクティブなMeshとModifier各1つです。
Shape KeyのNLA Trackと、置換前のShape Keyデータブロックを直接参照する外部データは移行しません。
Geometry Nodes、Boolean、Decimateなど、トポロジーに依存するModifierは、
すべてのShape Keyで完全に同じトポロジーが得られる場合のみ適用できます。

## Create Anchor

1. Armatureを選択してEdit Modeに入ります。
2. Boneチェーンを1つ以上選択します。
3. **3D Viewport > Sidebar > Panda Tool > Rig** を開きます。
4. **Create Anchor** をクリックします。

選択した各チェーンのルートに、TailがルートのHeadに接するAnchorを作成します。
ルートをAnchorのConnectedな子にし、元のルートにParentがある場合は、その関係をAnchorの上に保持します。
実行後は作成したAnchorが選択されます。操作全体を1回のUndoで戻せます。

## Disconnect Bones

1. Armatureを選択してEdit Modeに入ります。
2. Boneを1本以上選択します。
3. **3D Viewport > Sidebar > Panda Tool > Rig** を開きます。
4. **Disconnect Bones** をクリックします。

選択したEdit Boneの **Connected** のみを解除します。
Parent関係、BoneのTransform、アニメーションデータ、Constraint、未選択Boneは変更しません。
ボタンはArmatureのEdit Modeでのみ使用でき、1回のUndoで元に戻せます。

## Remove Constraints

1. Object ModeでObjectを1つ以上、またはPose ModeでPose Boneを1本以上選択します。
2. **3D Viewport > Sidebar > Panda Tool > Rig** を開きます。
3. **Remove Constraints** をクリックします。

選択対象のConstraintを、種類を問わずすべて削除します。
Object ModeではObject Constraint、Pose ModeではBone Constraintのみを削除し、未選択対象は変更しません。
現在のBlender Modeから処理対象を自動判定します。
それ以外のModeや未選択時はボタンを使用できません。設定項目や確認ダイアログはありません。

削除したConstraint数と選択Object／Bone数をInfoに表示します。
Constraintがない場合は **No constraints found.** と表示して正常終了します。
**Ctrl + Z** でConstraintを復元できます。
リンクデータとLibrary Overrideは対象外です。選択に含まれる場合は変更前に検出し、処理全体を安全に中止します。

Transformのベイクや補正は行いません。保存されているTransform、リグ構造、Parent関係、
Modifier、Action、Animation Key、Driverは編集しません。
ただしConstraintの削除により、評価後のポーズや見た目は変化する場合があります。
削除したConstraintを参照するアニメーションやDriverのパスはそのまま残り、
UndoでConstraintを復元するまで参照先が無効になる場合があります。

Blender 4.2 LTS ～ 5.1の互換性とアニメーションデータの保持のため、
Objectには`constraints.clear()`、Pose BoneにはBlender標準の`pose.constraints_clear()`を使用します。
Blender 5.1では個別の`remove()`が関連するアニメーションカーブやDriverも削除するため、使用していません。

## Convert Names to English

1. Object Modeで、処理したいモデルのObjectを選択します。
2. **3D Viewport > Sidebar > Panda Tool > Rig** を開きます。
3. **Convert Names to English** をクリックします。

**Bone → Shape Key → Material → Object** の順に名称を変換します。
選択ObjectのParentやArmature Modifierが参照するArmatureとそのBone、
選択したMeshのShape Key、割り当てられたMaterialも対象です。
Boneの選択状態には依存せず、対象Armatureの全Boneを確認します。設定項目やネットワーク通信はありません。

[内蔵辞書](panda_tool/name_dictionary.py)に登録した日本語・簡体字・既知英語Aliasを、
NFKC正規化後の名称全体で照合します。未知名は元の表記を保持します。
部分一致、曖昧一致、番号付き接尾辞の推測、Regexによる照合は行いません。
`腕_L`などは個別に登録したBone Aliasであり、接尾辞から自動生成する規則ではありません。
ZZZのShape Key変換先52項目は指定どおり使用します。
`MouthRight`、`MouthLeft`、`下眼上` → `Eyelid_Squint`もそのままの表記です。

現在の辞書の標準名はBone 84、Shape Key 52、Material 31、Object 16件です。
MMDの捩・IK・肩P/C・D/EX系は通常Boneと区別します。
指はMMDの番号（親指0～2、他の指1～3）を保持します。
番号なしの指、役割を推測する補助名、`髪影`・`髪2`・`前髪_透明`などの複合名は変更しません。
[辞書比較レポート](docs/dictionary-second-pass-comparison.md)に調査資料・採用・不採用を記録しました。
Shape Keyの52項目と既存Aliasは変更していません。

Material名は内蔵辞書に登録した日本語／中国語の既知Aliasを完全一致で変換します。
未知名やモデル独自の衣装Material名は変更しません。
今回の正式対応表では`眼白` → `Sclera`、`白目` → `EyeWhite`、
`眉` → `Brow`、`瞳` → `Iris`を区別し、他の既存Aliasを保持しています。
既存の衣装Aliasは維持し、今回の服飾名の追加は指定された`上衣` → `Top`、`袖` → `Sleeve`のみです。
[Material辞書追加の検証結果](docs/material-dictionary-update-validation.md)も参照してください。

**Basis** と基準となるShape Keyは対象外です。
名前が衝突する場合は安全にSkipし、`.001`などの名称を生成しません。
同じ名前空間内の複数Aliasが同じ変換先を要求する場合は、すべてSkipします。
Object／Materialは全データブロック、Bone／Shape Keyはそれぞれのコレクション内で衝突を確認します。
Boneの変換先と同名のVertex Groupがある場合も、ウェイトの紐づけを保護するためSkipします。
Infoにカテゴリ別の変換数と衝突数を表示します。

Blender標準Undo（**Ctrl + Z**）に対応し、変換後の再実行も安全です。
対象データ、関連する参照、アニメーションにLinked Data／Library Overrideが含まれる場合は、
名称変更前に操作全体を中止します。予期しない書き込み失敗時は、変更済みの名称を戻してから中止します。
Boneを参照するSINGLE_PROP Driverの配列要素パス（例：
`pose.bones["左腕捩"].rotation_euler[0]`）も、変更前に操作全体を中止します。
Blender 4.2／5.1がこのパスを自動更新しないためです。
ScalarプロパティのパスとTRANSFORMSのBone参照は保持テストの対象です。

独立した翻訳対象は4カテゴリのみです。リグを保持するため、Blender標準の名称変更に伴い、
Boneに紐づくVertex Group名、ConstraintのSubtarget、アニメーションやDriverのパスなどの参照は追従します。
Driver／Actionデータブロック、Keyframe、Weight、Geometry、UV、Shape Keyの値や設定、
MaterialのShaderやSlot、Transform、階層構造を保持します。
共有データは複製せず1回だけRenameし、既存の利用先を維持します。
その名称変更や標準の参照追従は、未選択の利用先にも影響する場合があります。
スクリプト内の文字列、Custom Property、外部DCC／Export用の対応表は翻訳しません。

Blender 4.2.23 LTS／5.1.1で、Shape Key正式表の全項目、参照、衝突、Undo、再実行を自動検証しています。
指定のYanagi原本はBlender 5形式のため、4.2では直接開けません。
4.2の実モデル検証はBlender 4.5 LTS経由で保存した検証用コピーを使います。
互換保存時の警告は、このOperatorの動作とは別の制限です。
原本にはShape Key Driverがないため、追加検証ではメモリ上のモデルコピーにDriverと
アニメーションを設定し、変換後も参照が保持されることを確認します。

## Delete Unregistered Bones

1. Object Modeで、リグに紐づくMesh Objectを1つアクティブにします。
2. **3D Viewport > Sidebar > Panda Tool > Rig** を開きます。
3. **Scan Unregistered Bones** をクリックして候補を確認します。
4. チェックを調整し、**Delete Checked Bones** をクリックします。

MeshのParentまたはArmature ModifierからArmatureを取得し、同名のVertex GroupがないBoneを候補にします。
Deform Boneは初期状態でチェックされます。Non-Deform Boneはコントローラーや補助Boneとして
使われることが多いため、初期状態では未チェックで、ロックの警告を表示します。
この警告は手動での選択を禁止するものではありません。**All**／**None** で候補全体のチェックを切り替えられます。

削除直前に再検証するため、Scan後に同名のVertex Groupを追加したBoneは残ります。
削除されるBoneの子は、残る最も近い祖先Boneに付け替えます。
Rest状態のHead、Tail、Roll、長さ、方向を保持します。
Parentを付け替えた子がConnectedの場合は、BlenderがHeadを移動させないよう必要に応じてConnectedを解除します。
操作全体を1回のUndoで戻せます。

ActionやFCurve内のBone参照、ConstraintのSubtarget、Driver、スクリプトの参照は書き換えません。
アニメーション済みのリグや制御リグでは、実行前に候補をよく確認してください。

## Remove Unused Vertex Groups Safe

1. Mesh Objectを1つアクティブにします。
2. **3D Viewport > Sidebar > Panda Tool > Vertex Groups** を開きます。
3. **Scan Unused Groups** をクリックしてチェック済みの候補を確認します。
4. 残したいGroupのチェックを外し、**Remove Unused Groups** をクリックします。

どの頂点にも正のウェイトが割り当てられていないGroupだけを候補にします。
対応するArmatureのBoneがないという理由だけでは未使用と判断しません。
Geometry Nodes、衣装、後の作業用に用意したGroupを、その理由だけで削除することはありません。
削除直前に選択したGroupを再検証し、実行後は候補を更新します。削除は1回のUndoで戻せます。

## 開発用テスト

Blenderに依存しない命名テストは、Repositoryのルートから実行できます。

```powershell
python -m unittest discover -s tests -v
```

統合テストはBlender本体で実行します。

```powershell
blender --background --factory-startup --python-exit-code 1 --python tests/blender_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/remove_constraints_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/convert_names_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/dictionary_second_pass_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/material_dictionary_integration.py
```

## Extensionパッケージのビルド

Repositoryのルートから`build.bat`を実行するか、Explorerでダブルクリックします。
Blender標準のExtensionビルドコマンドを使用し、`dist/panda_tool-0.8.0.zip`を生成します。

```powershell
.\build.bat
```

最初に`PATH`の`blender`を使用します。WindowsではBlender Foundationの標準インストール先も確認し、
Blender 5.1を優先します。独自のインストール先を使う場合は、実行前に`BLENDER_EXE`を指定してください。

```powershell
$env:BLENDER_EXE = 'D:\Apps\Blender\blender.exe'
.\build.bat
```

`dist/`内の生成ファイルはGit管理の対象外です。
Releaseと同じZIPを再パッケージせずにSILL-BILL Blender Extensions Repositoryで配布します。

## License

[GPL-3.0-only](LICENSE)。

## Maintainer・Repository情報

- Maintainer：**Gonsaku**
- ソース：[SILL-BILL/panda-tool-blender](https://github.com/SILL-BILL/panda-tool-blender)
- Release：[GitHub Releases](https://github.com/SILL-BILL/panda-tool-blender/releases)
- Extension Repository：[SILL-BILL/blender-extensions](https://github.com/SILL-BILL/blender-extensions)
