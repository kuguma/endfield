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
├── recipes.json                 # 生産レシピ・マシン電力データベース
└── docs/
    └── valley4_analysis.md      # 四号谷地 出荷製品の効率分析
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

### recipes.json

全28レシピと7種のマシン電力データ。

```json
{
  "machines": {
    "grinding_unit": { "name_en": "Grinding Unit", "power": 50 }
  },
  "recipes": {
    "sc_valley_battery": {
      "machine": "packaging_unit",
      "time_sec": 10,
      "inputs": { "ferrium_part": 10, "originium_powder": 15 },
      "outputs": { "sc_valley_battery": 1 }
    }
  }
}
```

## 効率分析

[四号谷地 出荷製品の効率分析](docs/valley4_analysis.md) では、各製品について：

- 原材料消費レート（フルレート生産時）
- 電力コストを含めた総コスト
- 実効利益率の比較

を算出しています。

### 主な発見

| 指標 | 最良の選択肢 |
|---|---|
| 実効利益率 | 中容量バッテリー (+13.8%) |
| 実効利益/min | 大容量バッテリー (+32.0/min) |
| 避けるべき製品 | カプセルⅠ / 缶詰Ⅰ (−24.1%) |

- Tier III 製品（カプセルⅢ/缶詰Ⅲ/大容量バッテリー）は Grinding Unit の電力コストが重く、見かけの利益率 (17-20%) から実効 4-8% まで低下
- 基礎素材（結晶外殻/紫晶ボトル/部品）は電力分だけ赤字になるため、そのまま出荷するより加工した方が良い場合もある

## データソース

- [Endfield Talos Wiki (wiki.gg)](https://endfield.wiki.gg/)
- [Game8 エンドフィールド攻略](https://game8.jp/arknights-endfield)

## ライセンス

データは攻略情報の引用・整理であり、ゲーム内データの著作権は Hypergryph / Gryphline に帰属します。
