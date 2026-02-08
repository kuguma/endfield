# 武陵 出荷製品の効率分析

武陵（Wuling）で拠点取引可能な全4製品について、原材料の採掘・栽培コストと生産チェーンの電力コストを考慮した実効利益率を分析する。

ポートフォリオ最適化については [optimization_problem.md](optimization_problem.md) を参照。

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

### 電力コストの算出方法

電力の機会コストを「LC Wuling Battery を売った場合の逸失利益」として計算する。

- **LC Wuling Battery**: 1,600 power × 40 sec = 64,000 unit·sec
- **LC Wuling Battery 取引券価値**: 25
- **電力単価**: 25 ÷ 64,000 ≈ **0.000391 券/unit·sec**

### 原材料の価値算出

#### 鉱石の材料価値

芽針注射剤Ⅰ（青鉄鉱のみ使用）を基準に算出：

| 原材料 | 基準製品 | 取引価格 | 採掘電力 | 材料価値 |
|---|---|--:|--:|--:|
| 青鉄鉱 | 芽針注射剤Ⅰ（÷20） | 16 | 0.012 | **0.749** |
| 源石鉱 | 小容量バッテリー（÷30） | - | 0.006 | **0.777** |

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

| 製品 | 速度 | 錦草 | 芽針 | 清水 | 青鉄鉱 | 源石鉱 | サンドリーフ | 息壌 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 息壌 | 30 | 15 | - | 30 | - | - | - | - |
| 錦草ソーダ | 6 | 15 | - | 30 | 120 | - | - | - |
| 芽針注射剤Ⅰ | 6 | - | 15 | 30 | 120 | - | - | - |
| 小容量武陵バッテリー | 6 | - | - | 30 | - | 180 | 30 | 30 |

※ 小容量武陵バッテリーの息壌(30/min)は内製を前提

### コスト内訳（1個あたり）

| 製品 | 単価 | 材料コスト | 採掘電力 | 栽培電力 | 加工電力 | 総コスト | 実効利益 | 利益率 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 息壌 | 1 | 0 | - | 0.022 | 0.061 | 0.083 | +0.917 | **+1105%** |
| 錦草ソーダ | 16 | 14.98 | 0.234 | 0.107 | 0.684 | 16.005 | −0.005 | ~0% |
| 芽針注射剤Ⅰ | 16 | 14.98 | 0.234 | 0.107 | 0.684 | 16.005 | −0.005 | ~0% |
| 小容量武陵バッテリー | 25 | 23.31 | 0.176 | 0.607 | 0.890 | 24.983 | +0.017 | ~0% |

### 実効利益ランキング

#### 利益率順

| 順位 | 製品 | 実効利益率 |
|--:|---|--:|
| 1 | 息壌 | **+1105%** |
| 2 | 小容量武陵バッテリー | ~0% |
| 3 | 錦草ソーダ / 芽針注射剤Ⅰ | ~0% |

#### 利益/min 順

| 順位 | 製品 | 実効利益/min |
|--:|---|--:|
| 1 | 息壌 | **+27.5** |
| 2 | 小容量武陵バッテリー | ~0 |
| 3 | 錦草ソーダ / 芽針注射剤Ⅰ | ~0 |

## 備考

### 息壌の特性

- 息壌は植物と水のみで製造でき、鉱石を消費しない
- 小容量武陵バッテリーの原材料として息壌5個が必要
- 生産レート制限: 天穹の炉の設置上限により最大60/min

### 地域間の電力コスト比較

| 地域 | バッテリー | 蓄電量 | 取引価格 | 電力単価 |
|---|---|--:|--:|--:|
| 四号谷地 | HC Valley | 44,000 | 70 | 0.00159 |
| 武陵 | LC Wuling | 64,000 | 25 | 0.000391 |

## チェーン電力の内訳

<details>
<summary>各製品のマシン構成（クリックで展開）</summary>

### 息壌 (77.5)
- Forge of the Sky ×1 = 50
- Refining ×2 (Stabilized Carbon) = 10
- Refining ×2 (Dense Carbon Powder) = 10
- Shredding ×1 (Carbon Powder) = 5
- Refining ×0.5 (Carbon from Jincao) = 2.5

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
- ※ Originium Powder の Shredding (30 power) は省略されている可能性あり

</details>

## データソース

- [Endfield Talos Wiki (wiki.gg)](https://endfield.wiki.gg/) - マシン電力、レシピデータ
- [Game8 エンドフィールド攻略](https://game8.jp/arknights-endfield) - 取引価格データ
- [recipes.json](../recipes.json) - 本リポジトリのレシピデータベース
- [wuling_products.json](../wuling_products.json) - 本リポジトリの製品データベース
