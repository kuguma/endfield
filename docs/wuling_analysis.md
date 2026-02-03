# 武陵 出荷製品の効率分析

武陵（Wuling）で拠点取引可能な全3製品について、原材料コストと電力コストを考慮した実効利益率を分析する。

## 結論

| 目的 | 推奨製品 | 理由 |
|---|---|---|
| 利益率重視 | **小容量武陵バッテリー** | 実効利益率 +11.7% で最高 |
| 利益総額重視 | **小容量武陵バッテリー** | 実効利益 +15.7/min で最高 |
| 避けるべき | 息壌（単体出荷） | 原価割れ −35.9% |

## 分析の前提

### 生産速度

| サイクル | マシン例 | 生産速度 |
|---|---|---|
| 2秒 | Refining / Shredding / Forge of the Sky / Reactor Crucible | 30個/min |
| 10秒 | Packaging | 6個/min |

### マシン電力

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

### 電力コストの算出方法

電力の機会コストを「LC Wuling Battery を売った場合の逸失利益」として計算する。

- **LC Wuling Battery**: 1,600 power × 40 sec = 64,000 unit·sec
- **LC Wuling Battery 取引券価値**: 25
- **電力単価**: 25 ÷ 64,000 ≈ **0.000391 券/unit·sec**

| 項目 | 計算式 |
|---|---|
| チェーン電力 | フルレート生産に必要な全マシンの消費電力合計 |
| エネルギー/個 | チェーン電力 × 60 ÷ 生産速度 |
| 電力コスト | エネルギー/個 × 25 ÷ 64,000 |
| 総コスト | 原価 + 電力コスト |
| 実効利益 | 単価 − 総コスト |
| 実効利益率 | 実効利益 ÷ 総コスト |

### 原材料の原価

武陵の一次原材料は以下の通り価値を1として計算する：
- 錦草 / 芽針（Jincao / Yazhen）: 1
- 清水（Clean Water）: 1
- 青鉄鉱（Ferrium Ore）: 1
- 源石鉱（Originium Ore）: 1
- サンドリーフ（Sandleaf）: 1

## 製品別分析

### 一覧表

| 製品 | 単価 | 速度 | 券/min | 錦草/芽針 | 清水 | 青鉄鉱 | 源石鉱 | サンドリーフ | 原価 | 電力 | 電力コスト | 総コスト | 実効利益 | 実効利益率 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 息壌 | 1 | 30 | 30 | 15 | 30 | - | - | - | 1.50 | 77.5 | 0.06 | 1.56 | −0.56 | −35.9% |
| 芽針注射剤Ⅰ | 16 | 6 | 96 | 15 | 30 | 120 | - | - | 27.50 | 175 | 0.68 | 28.18 | −12.18 | −43.2% |
| 小容量武陵バッテリー | 25 | 6 | 150 | 15 | 30 | - | 180 | 30 | 21.50 | 227.5 | 0.89 | 22.39 | +2.61 | **+11.7%** |

※ 原材料消費量は /min、原価は原材料1個=1として計算

### 実効利益ランキング

#### 利益率順

| 順位 | 製品 | 実効利益率 |
|--:|---|--:|
| 1 | 小容量武陵バッテリー | +11.7% |
| 2 | 息壌 | −35.9% |
| 3 | 芽針注射剤Ⅰ | −43.2% |

#### 利益/min 順

| 順位 | 製品 | 実効利益/min |
|--:|---|--:|
| 1 | 小容量武陵バッテリー | +15.7 |
| 2 | 息壌 | −16.8 |
| 3 | 芽針注射剤Ⅰ | −73.1 |

## 考察

### なぜ小容量武陵バッテリーが効率的か

- **取引単価が高い**: 25券（息壌の25倍、芽針注射剤Ⅰの1.56倍）
- **息壌を直接使用**: 息壌を単体で売るより、バッテリーに加工した方が価値が高い

### 芽針注射剤Ⅰの問題点

- **原価が高い**: 青鉄鉱を大量に消費（120/min）
- **取引単価が相対的に低い**: 原価27.5に対し単価16は原価割れ
- **回復アイテムとしての価値**: 取引ではなく戦闘消耗品として利用した方が良い

### 推奨戦略

1. **息壌を直接出荷しない**: 必ず小容量武陵バッテリーに加工してから出荷
2. **芽針注射剤Ⅰは自家消費用**: 取引に回すより戦闘で使用

## チェーン電力の内訳

<details>
<summary>各製品のマシン構成（クリックで展開）</summary>

### 息壌 (77.5)
- Forge of the Sky ×1 = 50
- Refining ×2 (Stabilized Carbon) = 10
- Refining ×2 (Dense Carbon Powder) = 10
- Shredding ×1 (Carbon Powder) = 5
- Refining ×0.5 (Carbon from Jincao/Yazhen) = 2.5

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

### 小容量武陵バッテリー (227.5)
- Packaging ×1 = 20
- Forge of the Sky ×1 (Xiranite) = 50
- Refining ×2 (Stabilized Carbon) = 10
- Refining ×2 (Dense Carbon Powder) = 10
- Shredding ×1 (Carbon Powder) = 5
- Refining ×0.5 (Carbon) = 2.5
- Grinding ×3 (Dense Originium Powder) = 150

</details>

## データソース

- [Endfield Talos Wiki (wiki.gg)](https://endfield.wiki.gg/) - マシン電力、レシピデータ
- [Game8 エンドフィールド攻略](https://game8.jp/arknights-endfield) - 取引価格データ
- [recipes.json](../recipes.json) - 本リポジトリのレシピデータベース
- [wuling_products.json](../wuling_products.json) - 本リポジトリの製品データベース
