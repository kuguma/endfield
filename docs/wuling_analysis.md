# 武陵 出荷製品の効率分析

武陵（Wuling）で拠点取引可能な全4製品について、原材料の採掘・栽培コストと生産チェーンの電力コストを考慮した実効利益率を分析する。

## 結論

| 目的 | 推奨製品 | 理由 |
|---|---|---|
| 避けるべき | 全製品 | 全て原価割れ |
| 損失最小 | **息壌** | 実効利益率 −36.7% で最もマシ |

**注意**: 原材料価値=1、息壌取引価格=1で計算すると、全製品が赤字となる。武陵の取引券システムは、原材料を「余剰処分」する目的に適している。

## 分析の前提

### 生産速度

| サイクル | マシン例 | 生産速度 |
|---|---|---|
| 2秒 | Refining / Shredding / Forge of the Sky / Reactor Crucible | 30個/min |
| 10秒 | Packaging | 6個/min |

### 採掘・栽培設備

| 設備 | 消費電力 | 生産レート | 用途 |
|---|--:|--:|---|
| Electric Mining Rig | 5 | 20/min | 源石鉱 |
| Electric Mining Rig Mk II | 10 | 20/min | 青鉄鉱 |
| Fluid Pump | 10 | 30/min | 清水 |
| Planting Unit | 20 | 60/min | 錦草/芽針（+清水） |
| Seed-Picking Unit | 10 | 30/min | 錦草/芽針の種取り |

※ 採掘レートは高純度鉱床（地域開発完了後）を前提

### 原材料1個あたりの電力エネルギー

| 原材料 | 計算式 | unit·sec |
|---|---|--:|
| 源石鉱 | 5 × 60 ÷ 20 | 15 |
| 青鉄鉱 | 10 × 60 ÷ 20 | 30 |
| 清水 | 10 × 60 ÷ 30 | 20 |
| 錦草/芽針 | (20+10) × 60 ÷ 30 + 10 ※清水込み | 70 |
| サンドリーフ | (40+10) × 60 ÷ 30 ※持続ループ | 100 |

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

### 電力コストの算出方法

電力の機会コストを「LC Wuling Battery を売った場合の逸失利益」として計算する。

- **LC Wuling Battery**: 1,600 power × 40 sec = 64,000 unit·sec
- **LC Wuling Battery 取引券価値**: 25
- **電力単価**: 25 ÷ 64,000 ≈ **0.000391 券/unit·sec**

| 項目 | 計算式 |
|---|---|
| 素材コスト | 素材価値 + 素材電力コスト |
| チェーン電力コスト | チェーン電力 × 60 ÷ 速度 × 電力単価 |
| 総コスト | 素材コスト + チェーン電力コスト |
| 実効利益 | 単価 − 総コスト |
| 実効利益率 | 実効利益 ÷ 総コスト |

### 原材料の評価

| 原材料 | 素材価値 | 電力コスト | 合計コスト |
|---|--:|--:|--:|
| 源石鉱 | 1 | 0.006 | 1.006 |
| 青鉄鉱 | 1 | 0.012 | 1.012 |
| 清水 | 1 | 0.008 | 1.008 |
| 錦草/芽針 | 1 | 0.027 | 1.027 |
| サンドリーフ | 1 | 0.039 | 1.039 |
| 息壌（取引価格） | 1 | - | 1.000 |

※ 小容量武陵バッテリーでは息壌を取引価格(1)で評価

## 製品別分析

### 一覧表

| 製品 | 単価 | 速度 | 錦草 | 芽針 | 清水 | 青鉄鉱 | 源石鉱 | サンドリーフ | 息壌 | 素材コスト | 素材電力 | チェーン電力 | 総コスト | 実効利益 | 実効利益率 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 息壌 | 1 | 30 | 15 | - | 30 | - | - | - | - | 1.50 | 0.02 | 0.06 | 1.58 | −0.58 | −36.7% |
| 錦草ソーダ | 16 | 6 | 15 | - | 30 | 120 | - | - | - | 27.50 | 0.35 | 0.68 | 28.53 | −12.53 | −43.9% |
| 芽針注射剤Ⅰ | 16 | 6 | - | 15 | 30 | 120 | - | - | - | 27.50 | 0.35 | 0.68 | 28.53 | −12.53 | −43.9% |
| 小容量武陵バッテリー | 25 | 6 | - | - | - | - | 180 | 30 | 30 | 40.00 | 0.38 | 0.59 | 40.97 | −15.97 | −38.9% |

※ 原材料消費量は /min
※ 小容量武陵バッテリーは息壌(30/min)を取引価格(1)で評価、息壌製造の電力を除外

### 実効利益ランキング

#### 利益率順（損失率の低い順）

| 順位 | 製品 | 実効利益率 |
|--:|---|--:|
| 1 | 息壌 | −36.7% |
| 2 | 小容量武陵バッテリー | −38.9% |
| 3 | 錦草ソーダ / 芽針注射剤Ⅰ | −43.9% |

#### 損失/min 順

| 順位 | 製品 | 実効利益/min |
|--:|---|--:|
| 1 | 息壌 | −17.4 |
| 2 | 錦草ソーダ / 芽針注射剤Ⅰ | −75.2 |
| 3 | 小容量武陵バッテリー | −95.8 |

## 考察

### なぜ全製品が赤字なのか

武陵の取引システムは原材料価値に対して取引価格が低く設定されている：

| 製品 | 原材料価値 | 取引価格 | 価値比 |
|---|--:|--:|--:|
| 息壌 | 1.5 | 1 | 67% |
| 錦草ソーダ | 27.5 | 16 | 58% |
| 芽針注射剤Ⅰ | 27.5 | 16 | 58% |
| 小容量武陵バッテリー | 40 | 25 | 63% |

### 息壌が最もマシな理由

- **チェーン電力が最小**: 77.5（バッテリーの34%）
- **損失/min が最小**: −17.4/min（バッテリーの18%）

### 錦草ソーダ / 芽針注射剤Ⅰの問題点

- **原価が高い**: 青鉄鉱を大量に消費（120/min）
- **取引単価が相対的に低い**: 原価27.5に対し単価16は原価割れ
- **回復アイテムとしての価値**: 取引ではなく戦闘消耗品として利用した方が良い

### 推奨戦略

1. **武陵の取引は「余剰処分」**: 原材料を売る手段として利用（利益を期待しない）
2. **損失を最小化するなら息壌**: 加工せずに直接出荷
3. **錦草ソーダ / 芽針注射剤Ⅰは自家消費用**: 取引に回すより戦闘で使用

## チェーン電力の内訳

<details>
<summary>各製品のマシン構成（クリックで展開）</summary>

### 息壌 (77.5)
- Forge of the Sky ×1 = 50
- Refining ×2 (Stabilized Carbon) = 10
- Refining ×2 (Dense Carbon Powder) = 10
- Shredding ×1 (Carbon Powder) = 5
- Refining ×0.5 (Carbon from Jincao/Yazhen) = 2.5

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
