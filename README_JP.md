# Panda Tool Blender

[English](README.md) | 日本語

Panda Toolは、Blenderでのアニメーション制作やリギングを効率化する、
小さな実用ツールのコレクションです。v0.7.0で **Remove Constraints** を追加しました。

## 機能一覧

- **Panda Apply Modifier**：Shape Keysを保持してModifierを1つ適用します。現在のArmatureのポーズのベイクにも対応します。
- **Create Anchor**：選択したBoneチェーンのルートにAnchorを追加します。
- **Disconnect Bones**：選択したEdit BoneのConnectedを解除します。
- **Remove Constraints**：選択したObjectまたはPose BoneのConstraintをすべて削除します。
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

1. [v0.7.0のRelease](https://github.com/SILL-BILL/panda-tool-blender/releases/tag/v0.7.0)から
   `panda_tool-0.7.0.zip`をダウンロードするか、ローカルでビルドします。
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
```

## Extensionパッケージのビルド

Repositoryのルートから`build.bat`を実行するか、Explorerでダブルクリックします。
Blender標準のExtensionビルドコマンドを使用し、`dist/panda_tool-0.7.0.zip`を生成します。

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
