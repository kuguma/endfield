# CLAUDE.md

このファイルは Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

アークナイツ：エンドフィールドの生産最適化ツールキット。製品・レシピデータベース（JSON）と、各地域の取引券生産レートを最大化する最適ポートフォリオを求めるLPソルバーを提供する。

## ソルバーの実行

```bash
# 四号谷地、24時間売却間隔で最適ポートフォリオを計算
python scripts/solve_portfolio.py valley_iv 24

# 武陵、12時間間隔
python scripts/solve_portfolio.py wuling 12

# 地域エイリアス: "valley_iv", "valley4", "wuling"
# 時間引数は手動売却間隔（時間単位: 12, 24, 48, 72, 168）
```

```bash
# 電力消費計算の検証
python scripts/verify_power.py
```

## 依存関係

Python 3.10+ / `numpy` / `scipy`（requirements.txt なし — `pip install numpy scipy` で手動インストール）

## アーキテクチャ

### データ層（JSON）
- `valley4_products.json` / `wuling_products.json` — 地域設定: 採掘レート、貯蓄上限、拠点定義（取引券蓄積レート/上限）、出荷製品カタログ
- `recipes.json` — マシン定義（10種、電力コスト付）、アイテム定義（65種以上）、レシピチェーン（39レシピ、入出力とサイクルタイム）。一部のアイテム/マシンは `"region"` フィールドで地域限定

### ソルバー (`scripts/solve_portfolio.py`)
中核スクリプト。地域JSON + レシピを読み込み、LP制約を構築し `scipy.optimize.milp` で解く。

データフロー:
1. `load_region_data()` — JSON解析、レシピチェーンを再帰的にたどり製品ごとの鉱石消費量・電力コストを算出
2. `build_lp()` — 制約行列を構築: 鉱石制限、電力収支、貯蓄容量、拠点取引券蓄積、製品-拠点割当
3. 複数の時間間隔で解を求め、0.25刻みの電力配分でマシン台数を出力

重要なドメイン概念:
- **電力は機会費用** — 生産に使わない電力はバッテリーとして売却可能なため、取引券換算のコストが存在する
- **拠点の取引券蓄積**が生産能力ではなく律速制約になることが多い
- **バッテリーは製品であり電力源でもある** — LPにフィードバックループを生む

### 電力検証 (`scripts/verify_power.py`)
生産チェーンをたどって電力消費を独立検証するユーティリティ。マシンデータをハードコード（recipes.json非依存）。

### ドキュメント (`docs/`)
- `optimization_problem.md` — 7つの制約カテゴリを含むLP定式化
- `*_analysis.md` — 製品ごとの効率ランキングとコスト内訳
- `optimization_solved_*.md` — 整数・0.5・0.25刻みの事前計算済み最適解

## データ規約

- 生産レートは「マシン1台増分あたり毎分」で正規化
- 電力は unit/sec
- 取引価格は地域固有の取引券（券）
- 鉱石: 源石鉱 (originium)、紫晶鉱 (amethyst)、青鉄鉱 (ferrium)
- 地域: 四号谷地 (Valley IV)、武陵 (Wuling)
