# 武陵 出荷製品の効率分析

武陵（Wuling）で拠点取引可能な全製品について、原材料の採掘・栽培コストと生産チェーンの電力コストを考慮した実効利益率を分析する。

**v1.2対応** (2026-04-17): 重息壌、緋銅部品、錦草ソーダⅡを追加。新拠点「心臓修復施設」追加。天有洪炉8台、赤銅鉱180/min、沈殿酸240/min。

**v1.1対応**: 赤銅部品、中容量武陵バッテリー、芽針注射剤Ⅱを追加。

ポートフォリオ最適化については [optimization_problem.md](optimization_problem.md) を参照。

## 分析の前提

### 生産速度

| サイクル | マシン例 | 生産速度 |
|---|---|---|
| 2秒 | Refining / Shredding / Forge of the Sky / Reactor Crucible / Fitting / Moulding / Filling | 30個/min |
| 10秒 | Packaging / Gearing | 6個/min |

### 採掘・栽培設備

| 設備 | 消費電力 | 生産レート | 用途 |
|---|--:|--:|---|
| Electric Mining Rig | 5 | 20/min | 源石鉱 |
| Electric Mining Rig Mk II | 10 | 20/min | 青鉄鉱 |
| Hydro Mining Rig | 0 (清水駆動) | 30/min | 赤銅鉱 |
| Fluid Pump | 10 | 30/min | 清水 |
| Planting Unit | 20 | 60/min | 錦草/芽針（+清水） |
| Seed-Picking Unit | 10 | 30/min | 錦草/芽針の種取り |

※ 採掘レートは高純度鉱床（地域開発完了後）を前提
※ 水力採鉱機は電力不要、清水をパイプで供給して動作

### 原材料1個あたりの電力エネルギー

| 原材料 | 計算式 | unit·sec |
|---|---|--:|
| 源石鉱 | 5 × 60 ÷ 20 | 15 |
| 青鉄鉱 | 10 × 60 ÷ 20 | 30 |
| 赤銅鉱 | Fluid Pump 10 × 60 ÷ 30 ※清水経由 | 20 |
| 清水 | 10 × 60 ÷ 30 | 20 |
| 錦草/芽針 | (20+10) × 60 ÷ 30 + 10 ※清水込み | 70 |
| サンドリーフ | (20+10) × 60 ÷ 30 ※持続ループ | 100 |

### 生産マシン電力

| マシン | 消費電力 |
|---|--:|
| Shredding Unit | 5 |
| Refining Unit | 5 |
| Moulding Unit | 10 |
| Fitting Unit | 20 |
| Filling Unit | 20 |
| Packaging Unit | 20 |
| Grinding Unit | 50 |
| Forge of the Sky | 50 |
| Reactor Crucible | 50 |
| Gearing Unit | 10 |

### 電力コストの算出方法

電力の機会コストを「小容量武陵バッテリーを売った場合の逸失利益」として計算する。

- **小容量武陵バッテリー**: 1,600 power × 40 sec = 64,000 unit·sec
- **取引券価値**: 25
- **電力単価**: 25 ÷ 64,000 ≈ **0.000391 券/unit·sec**

### 原材料の価値算出

#### 鉱石の材料価値

芽針注射剤Ⅰ（青鉄鉱のみ使用）を基準に算出：

| 原材料 | 基準製品 | 取引価格 | 採掘電力 | 材料価値 |
|---|---|--:|--:|--:|
| 青鉄鉱 | 芽針注射剤Ⅰ（÷20） | 16 | 0.012 | **0.749** |
| 源石鉱 | 小容量バッテリー（÷30） | - | 0.006 | **0.777** |
| 赤銅鉱 | 赤銅部品（÷1） ※注 | 1 | 0.008 | **~0** |

※ 赤銅鉱の材料価値: 赤銅部品（1券）から電力コストを差し引くとほぼ0。赤銅鉱は水力採鉱で電力不要だが清水が必要。

※ 源石鉱の価値は小容量武陵バッテリーから息壌・サンドリーフのコストを差し引いて算出

#### 植物・水の材料価値

植物と水は電力があれば無限に生産できるため、**材料価値は0**。コストは電力のみ。

| 原材料 | 材料価値 | 電力コスト |
|---|--:|--:|
| 錦草/芽針 | 0 | 0.027 |
| 清水 | 0 | 0.008 |
| サンドリーフ | 0 | 0.039 |

### コスト計算式

| 項目 | 計算式 |
|---|---|
| 材料コスト | Σ(鉱石数量 × 鉱石材料価値) |
| 採掘電力コスト | Σ(鉱石数量 × 採掘電力 × 電力単価) |
| 栽培電力コスト | Σ(植物/水 数量 × 電力 × 電力単価) |
| 加工電力コスト | チェーン電力 × 60 ÷ 速度 × 電力単価 |
| 総コスト | 材料コスト + 全電力コスト |
| 実効利益 | 単価 − 総コスト |
| 実効利益率 | 実効利益 ÷ 総コスト |

## 製品別分析

### 原材料消費量（/min）

| 製品 | 速度 | 錦草 | 芽針 | 清水 | 青鉄鉱 | 源石鉱 | 赤銅鉱 | サンドリーフ | 息壌 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 息壌 | 30 | 15 | - | 30 | - | - | - | - | - |
| 赤銅部品 | 30 | - | - | 30 | - | - | 30 | - | - |
| 錦草ソーダ | 6 | 15 | - | 30 | 120 | - | - | - | - |
| 芽針注射剤Ⅰ | 6 | - | 15 | 30 | 120 | - | - | - | - |
| 芽針注射剤Ⅱ | 6 | - | 15 | 180 | - | - | 120 | - | - |
| 小容量武陵バッテリー | 6 | - | - | 30 | - | 180 | - | 30 | 30 |
| 中容量武陵バッテリー | 6 | 30 | - | 150 | 30 | 240 | 30 | 40 | ※60 |

※ 小容量武陵バッテリーの息壌(30/min)は内製を前提
※ 中容量武陵バッテリーは息壌60/min（壌晶チェーン用）を内製。汚水は赤銅精錬から30/min調達
※ 芽針注射剤Ⅱは赤銅製ボトルを使用（鉄青不要）。清水は赤銅精錬用120 + 芽針溶液用30 + 赤銅ボトル用30 = 180

### コスト内訳（1個あたり）

| 製品 | 単価 | 材料コスト | 採掘電力 | 栽培電力 | 加工電力 | 総コスト | 実効利益 | 利益率 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 息壌 | 1 | 0 | - | 0.022 | 0.061 | 0.083 | +0.917 | **+1105%** |
| 赤銅部品 | 1 | ~0 | 0.016 | 0.008 | 0.020 | 0.043 | +0.957 | **+2200%** |
| 錦草ソーダ | 16 | 14.98 | 0.234 | 0.107 | 0.684 | 16.005 | −0.005 | ~0% |
| 芽針注射剤Ⅰ | 16 | 14.98 | 0.234 | 0.107 | 0.684 | 16.005 | −0.005 | ~0% |
| 芽針注射剤Ⅱ | 22 | ~0 | 0.156 | 0.133 | 0.645 | 0.934 | +21.07 | **+2256%** |
| 小容量武陵バッテリー | 25 | 23.31 | 0.176 | 0.607 | 0.890 | 24.983 | +0.017 | ~0% |
| 中容量武陵バッテリー | 54 | 18.65 + ~0 | 0.464 | 0.922 | 2.686 | 22.72 | +31.28 | **+138%** |

※ 赤銅部品と芽針注射剤Ⅱは赤銅鉱のみ消費。赤銅鉱の材料価値が極めて低いため高利益率。
※ 中容量バッテリーは源石鉱(材料価値高) + 青鉄鉱 + 赤銅鉱を消費。複雑なチェーンだが高単価で利益大。

### 実効利益ランキング

#### 利益率順

| 順位 | 製品 | 実効利益率 |
|--:|---|--:|
| 1 | 芽針注射剤Ⅱ | **+2256%** |
| 2 | 赤銅部品 | **+2200%** |
| 3 | 息壌 | **+1105%** |
| 4 | 中容量武陵バッテリー | **+138%** |
| 5 | 小容量武陵バッテリー | ~0% |
| 6 | 錦草ソーダ / 芽針注射剤Ⅰ | ~0% |

#### 利益/min 順

| 順位 | 製品 | 実効利益/min |
|--:|---|--:|
| 1 | 中容量武陵バッテリー | **+187.7** |
| 2 | 芽針注射剤Ⅱ | **+126.4** |
| 3 | 赤銅部品 | **+28.7** |
| 4 | 息壌 | **+27.5** |
| 5 | 小容量武陵バッテリー | ~0 |
| 6 | 錦草ソーダ / 芽針注射剤Ⅰ | ~0 |

## 備考

### v1.1 新製品の特徴

#### 赤銅部品
- 赤銅鉱＋清水のみで製造。鉱石材料価値がほぼ0のため利益率は極めて高い
- ただし単価1券のため絶対利益は小さい

#### 芽針注射剤Ⅱ
- 鉄青製→赤銅製ボトルに変更。青鉄鉱を消費しない
- 赤銅鉱120/min消費（Ⅰの青鉄120/minの代替）
- 単価22券（Ⅰの16券から+37.5%）で、赤銅鉱は低コストなので高効率

#### 中容量武陵バッテリー
- 壌晶（Xircon）を使用する新チェーン: 息壌→液化息壌→壌晶廃液→壌晶
- 汚水が中間体として必要（赤銅精錬の副産物として調達）
- 3,200 power × 40 sec = 128,000 unit·sec（小容量の2倍）
- 息壌60/min消費（天有洪炉の全容量を使用）→ 他の息壌消費製品と排他

### 息壌の特性

- 息壌は植物と水のみで製造でき、鉱石を消費しない
- 小容量武陵バッテリーの原材料として息壌5個が必要
- 中容量武陵バッテリーの壌晶チェーンで息壌10個（60/min）を消費
- 生産レート制限: 天有洪炉の設置上限により最大120/min（v1.1: 洪炉拡張Ⅱで4台）

### 赤銅鉱の特性

- 水力採鉱機（Hydro Mining Rig）で採掘。電力不要、清水で駆動
- 清波砦に全8台設置可能、合計120/min
- 赤銅精錬時に汚水が副産物として発生（中容量バッテリーの壌晶チェーンで利用可能）

### 汚水（Sewage）の役割

- 赤銅精錬の副産物: 赤銅鉱物 + 清水 → 赤銅塊 + **汚水**
- 壌晶の生産に必要: 液化息壌 + **汚水** → 壌晶廃液
- 壌晶の生産でも副産物: 壌晶廃液 + 鉄青パウダー → 壌晶 + **汚水**
- 中容量バッテリー生産時、赤銅精錬と壌晶生産の両方から汚水を確保する循環構造

### 地域間の電力コスト比較

| 地域 | バッテリー | 蓄電量 | 取引価格 | 電力単価 |
|---|---|--:|--:|--:|
| 四号谷地 | HC Valley | 44,000 | 70 | 0.00159 |
| 武陵 | 小容量武陵 | 64,000 | 25 | 0.000391 |
| 武陵 | 中容量武陵 | 128,000 | 54 | 0.000422 |

## チェーン電力の内訳

<details>
<summary>各製品のマシン構成（クリックで展開）</summary>

### 息壌 (77.5)
- Forge of the Sky ×1 = 50
- Refining ×2 (Stabilized Carbon) = 10
- Refining ×2 (Dense Carbon Powder) = 10
- Shredding ×1 (Carbon Powder) = 5
- Refining ×0.5 (Carbon from Jincao) = 2.5

### 赤銅部品 (25)
- Fitting ×1 (Cuprium Part) = 20
- Refining ×1 (Cuprium) = 5

### 錦草ソーダ (175)
- Packaging ×1 = 20
- Fitting ×2 (Ferrium Part) = 40
- Refining ×2 (Ferrium for Part) = 10
- Moulding ×1 (Ferrium Bottle) = 10
- Refining ×2 (Ferrium for Bottle) = 10
- Filling ×1 (Ferrium Bottle Jincao Solution) = 20
- Reactor Crucible ×1 (Jincao Solution) = 50
- Shredding ×0.5 (Jincao Powder) = 2.5
- Refining ×2.5 (extra Ferrium) = 12.5

### 芽針注射剤Ⅰ (175)
- Packaging ×1 = 20
- Fitting ×2 (Ferrium Part) = 40
- Refining ×2 (Ferrium for Part) = 10
- Moulding ×1 (Ferrium Bottle) = 10
- Refining ×2 (Ferrium for Bottle) = 10
- Filling ×1 (Ferrium Bottle Yazhen Solution) = 20
- Reactor Crucible ×1 (Yazhen Solution) = 50
- Shredding ×0.5 (Yazhen Powder) = 2.5
- Refining ×2.5 (extra Ferrium) = 12.5

### 芽針注射剤Ⅱ (165)
- Packaging ×1 = 20
- Fitting ×2 (Cuprium Part) = 40
- Refining ×2 (Cuprium for Part) = 10
- Filling ×1 (Cuprium Bottle Yazhen Solution) = 20
- Moulding ×1 (Cuprium Bottle) = 10
- Refining ×2 (Cuprium for Bottle) = 10
- Reactor Crucible ×1 (Yazhen Solution) = 50
- Shredding ×0.5 (Yazhen Powder) = 5

### 小容量武陵バッテリー (227.5)
- Packaging ×1 = 20
- Forge of the Sky ×1 (Xiranite) = 50
- Refining ×2 (Stabilized Carbon) = 10
- Refining ×2 (Dense Carbon Powder) = 10
- Shredding ×1 (Carbon Powder) = 5
- Refining ×0.5 (Carbon) = 2.5
- Grinding ×3 (Dense Originium Powder) = 150
- Shredding ×6 (Originium Powder) = ※省略（バッファに含む）

### 中容量武陵バッテリー (686.67)
- Packaging ×1 = 20
- **壌晶チェーン:**
  - Reactor Crucible ×1 (Xircon) = 50
  - Shredding ×1 (Ferrium Powder) = 5
  - Refining ×1 (Ferrium) = 5
  - Reactor Crucible ×2 (Xircon Effluent) = 100
  - Reactor Crucible ×2 (Liquid Xiranite) = 100
- **息壌チェーン** (60/min):
  - Forge of the Sky ×2 = 100
  - Refining ×4 (Stabilized Carbon) = 20
  - Refining ×4 (Dense Carbon Powder) = 20
  - Shredding ×2 (Carbon Powder) = 10
  - Refining ×1 (Carbon from Jincao) = 5
- **汚水源:**
  - Refining ×1 (Cuprium for Sewage) = 5
- **高純度源石パウダーチェーン** (120/min):
  - Grinding ×4 (Dense Originium Powder) = 200
  - Shredding ×8 (Originium Powder) = 40
  - Shredding ×1.33 (Sandleaf Powder) = 6.67

</details>

## v1.2 追加製品

### 重息壌 (Heavy Xiranite) — 27券

- **マシン**: Forge of the Sky 10s, Xiranite ×10 + Xircon Effluent ×5 → Heavy Xiranite ×1
- **生産**: 1台で 6/min。Xiranite 60/min + Xircon Effluent 30/min 入力
- **売却拠点**: 心臓修復施設 (Cardiac Remediation Station)
- **電力**: 415 unit/sec @ 6/min
- 鉱石不要 (息壌チェーン経由で炭素 = 錦草/芽針 から作る)、Sewage 30/min は他製品から調達
- 単独では利益率は中容量武陵バッテリーより劣るが、**心臓修復施設の蓄積率枠を埋める** のに最適

### 緋銅部品 (Hetonite Part) — 48券

- **マシン**: Fitting Unit 10s, Hetonite ×5 → Hetonite Part ×1
- **生産**: 1台で 6/min。Hetonite 30/min 入力
- **売却拠点**: 天王原 Lv3
- **電力**: 835 unit/sec @ 6/min (沈殿酸チェーンが大きい)
- **必要素材**: 赤銅鉱 20/個、青鉄鉱 5/個、沈殿酸 30/個 (純消費)
- **生産チェーン**:
  - Cuprium Ore + Clean Water → Cuprium (Refining)
  - Cuprium → Cuprium Powder (Shredding)
  - Cuprium Powder + Precipitation Acid → Cuprium Solution (Reactor Crucible)
  - Cuprium Solution ×4 → Hetonite Solution + Precipitation Acid (Purification Unit)
  - Hetonite Solution ×2 + Ferrium Powder → Hetonite + Sewage (Reactor Crucible)
  - Hetonite ×5 → Hetonite Part (Fitting)
- **副産物**: Sewage 20/個 (他の Cuprium 製品の Sewage と合算)
- **沈殿酸の純消費**: 30/個 (4個入力 - 1個副産物 = 3 PA per Hetonite Solution、それを ×10倍で Hetonite Part 1個)

### 錦草ソーダⅡ (Jincao Tea) — 22券

- 既存レシピ (v1.1) だが、v1.2 で取引対象に追加
- **マシン**: Packaging Unit 10s, Cuprium Part ×10 + Cuprium Bottle (Jincao Solution) ×5 → Jincao Tea ×1
- **売却拠点**: 心臓修復施設

## v1.2 期間限定: 息壌ひょうたん (Xiranite Gourd)

- **取引価格**: 武陵取引券 40 + 支援成果券 10
- **マシン**: Packaging Unit 10s, Experimental Xiranite Bottle ×5 + Experimental Xiranite Part ×5 → Xiranite Gourd ×1
- **必要素材**: Xiranite 15/個 (Bottle 10 + Part 5)
- **売却拠点**: 心臓修復施設
- **イベント期間**: AIC Support: Palm-Top Savior (〜2026-05-13)
- **電力**: 305 unit/sec @ 6/min

## v1.2 新マシン

| マシン | 電力 | 用途 |
|---|--:|---|
| 精製ユニット (Purification Unit) | 50 (推定) | Cuprium Solution → Hetonite Solution + 沈殿酸 |
| 拡張化学反応炉 (Expanded Crucible) | 100 (推定) | Reactor Crucible 上位互換 |
| 耐酸性液体ポンプMk II | 20 | 沈殿酸 30/min 抽出 (清水不要) |

## v1.2 ポートフォリオ最適化

[最適生産ポートフォリオ：武陵 (v1.2)](optimization_solved_wuling.md) を参照。

主要結果（24H、+30%ボーナス、心臓修復 Lv2）:

| 拠点 | 蓄積/h (×1.3) | 売却/min | 主力製品 |
|---|--:|--:|---|
| 天王原 (Lv3) | 34,944 | 582.40 | 緋銅部品 + 小容量バッテリー |
| 心臓修復施設 (Lv2) | 10,920 | 182.00 | 中容量バッテリー + 息壌 |
| **合計** | 45,864 | **764.40 券/min** | |

実効レート: v1.1 (582/min, 1拠点律速) → v1.2 (764.4/min, 2拠点律速) で **+31.3%**。

v1.1 では生産能力 723/min を 1 拠点の蓄積率上限 (582/min) で削っていた。v1.2 で心臓修復施設追加により蓄積率上限が +31% に拡大、生産能力も新製品で追従。

## データソース

- [Endfield Talos Wiki (wiki.gg)](https://endfield.wiki.gg/) - マシン電力、レシピデータ、拠点仕様
- [Game8 エンドフィールド攻略](https://game8.jp/arknights-endfield) - 取引価格データ
- [GameWith エンドフィールド](https://gamewith.net/akendfield/) - バッテリー電力仕様
- [biligame wiki 終末地](https://wiki.biligame.com/zmd/) - 仓储节点・設備図鑑
- [AppMedia エンドフィールド](https://appmedia.jp/arknights_endfield/) - 設備仕様
- [recipes.json](../recipes.json) - 本リポジトリのレシピデータベース
- [wuling_products.json](../wuling_products.json) - 本リポジトリの製品データベース
