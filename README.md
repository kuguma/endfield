# Arknights: Endfield Database

アークナイツ：エンドフィールドの製品・レシピデータベースと効率分析。

## 概要

このリポジトリは以下を提供します：

1. **製品データベース** - 拠点取引で出荷可能な製品の一覧と取引券価格
2. **レシピデータベース** - 一次原材料から最終製品までの全生産チェーン
3. **効率分析** - 電力コストを含めた実効利益率の比較

## ファイル構成

```
endfield_db/
├── README.md                    # このファイル
├── valley4_products.json        # 四号谷地の出荷製品データベース
├── wuling_products.json         # 武陵の出荷製品データベース
├── recipes.json                 # 生産レシピ・マシン電力データベース
└── docs/
    ├── valley4_analysis.md      # 四号谷地 出荷製品の効率分析
    └── wuling_analysis.md       # 武陵 出荷製品の効率分析
```

## データベース

### valley4_products.json

四号谷地（Valley IV）で拠点取引可能な全14製品。

```json
{
  "id": "sc_valley_battery",
  "name_ja": "中容量谷地バッテリー",
  "name_en": "SC Valley Battery",
  "trade_value": 30
}
```

### wuling_products.json

武陵（Wuling）で拠点取引可能な全4製品。

```json
{
  "id": "lc_wuling_battery",
  "name_ja": "小容量武陵バッテリー",
  "name_en": "LC Wuling Battery",
  "trade_value": 25
}
```

### recipes.json

全39レシピと10種のマシン電力データ（四号谷地・武陵共通）。

```json
{
  "machines": {
    "grinding_unit": { "name_en": "Grinding Unit", "power": 50 },
    "forge_of_the_sky": { "name_en": "Forge of the Sky", "power": 50, "region": "wuling" }
  },
  "recipes": {
    "xiranite": {
      "machine": "forge_of_the_sky",
      "time_sec": 2,
      "inputs": { "stabilized_carbon": 2, "clean_water": 1 },
      "outputs": { "xiranite": 1 },
      "region": "wuling"
    }
  }
}
```

## 効率分析

採掘・栽培の電力コストを含めた完全なコスト分析を行っています。

### 四号谷地

[四号谷地 出荷製品の効率分析](docs/valley4_analysis.md) では、全14製品について原材料消費レート、電力コスト、実効利益率を算出しています。

| 指標 | 最良の選択肢 |
|---|---|
| 実効利益率 | 中容量バッテリー (+10.3%) |
| 実効利益/min | 中容量バッテリー (+16.9/min) |
| 避けるべき製品 | カプセルⅠ / 缶詰Ⅰ (−27.6%) |

**主な発見:**
- 植物の栽培電力コストが重く、蕎花/シトローム/サンドリーフを使う製品は軒並み赤字
- 利益が出るのは中容量バッテリー (+10.3%)、鋼製部品 (+7.5%)、大容量バッテリー (+3.4%) の3製品のみ

### 武陵

[武陵 出荷製品の効率分析](docs/wuling_analysis.md) では、全4製品について同様の分析を行っています。

| 指標 | 結果 |
|---|---|
| 全製品 | 原価割れ（赤字） |
| 損失最小 | 息壌 (−36.7%) |
| 損失最大 | 芽針注射剤Ⅰ (−43.9%) |

**主な発見:**
- 武陵の取引は「余剰原材料の処分」目的で利用すべき（利益を期待しない）
- 芽針注射剤Ⅰは取引より戦闘消耗品として使用した方が効率的

## データソース

- [Endfield Talos Wiki (wiki.gg)](https://endfield.wiki.gg/)
- [Game8 エンドフィールド攻略](https://game8.jp/arknights-endfield)

## ライセンス

データは攻略情報の引用・整理であり、ゲーム内データの著作権は Hypergryph / Gryphline に帰属します。
