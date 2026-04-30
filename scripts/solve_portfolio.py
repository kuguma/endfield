#!/usr/bin/env python3
"""
Linear Programming solver for Endfield production optimization.

This script uses LP to find the optimal production portfolio that maximizes
trade ticket production rate given resource constraints.

Usage:
    python solve_portfolio.py valley_iv 24
    python solve_portfolio.py wuling 12
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linprog, milp, OptimizeResult, Bounds, LinearConstraint


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Product:
    """Represents a sellable product with its resource requirements."""
    id: str
    name_ja: str
    name_en: str
    trade_value: int
    production_rate: float  # items per minute at 1 machine increment
    originium_ore: float = 0.0  # ore consumption per minute at production_rate
    amethyst_ore: float = 0.0
    ferrium_ore: float = 0.0
    cuprium_ore: float = 0.0
    precipitation_acid: float = 0.0  # NET precipitation acid consumption per minute (mining demand)
    power_consumption: float = 0.0  # unit/sec at production_rate
    production_limit: float | None = None  # max production rate if limited
    is_battery: bool = False
    battery_power: float = 0.0  # power output per battery (unit/sec)
    # Intermediate material requirements (for Wuling)
    xiranite_consumption: float = 0.0  # xiranite consumed per minute at production_rate
    sandleaf_consumption: float = 0.0  # sandleaf consumed per minute at production_rate
    sewage_production: float = 0.0  # sewage produced per minute at production_rate (from cuprium refining)
    sewage_consumption: float = 0.0  # net sewage consumed per minute at production_rate
    # v1.2: outpost assignment - which outposts can sell this product
    sold_at: list[str] = field(default_factory=list)
    # Secondary currency (for event items like Xiranite Gourd)
    secondary_currency_value: float = 0.0  # e.g. AIC certs per unit


@dataclass
class RegionData:
    """Region-specific data including mining rates and products."""
    id: str
    name_ja: str
    name_en: str
    mining_rates: dict[str, float]
    storage_limit: int
    products: list[Product]
    outposts: list[dict[str, Any]]
    power_buffer: float = 2000.0  # unit/sec reserved for map facilities
    precipitation_acid_supply: float = 0.0  # /min from Acid Resistant Pump Mk II


# =============================================================================
# Data Loading
# =============================================================================

def load_region_data(region_id: str, base_path: Path) -> RegionData:
    """Load region data from JSON files and compute resource consumption."""

    # Map region IDs to file names
    region_files = {
        "valley_iv": "valley4_products.json",
        "valley4": "valley4_products.json",
        "wuling": "wuling_products.json",
    }

    filename = region_files.get(region_id.lower())
    if not filename:
        raise ValueError(f"Unknown region: {region_id}")

    json_path = base_path / filename
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    region_info = data["region"]

    # Define product specifications based on analysis docs
    if region_id.lower() in ("valley_iv", "valley4"):
        products = _build_valley4_products()
    elif region_id.lower() == "wuling":
        products = _build_wuling_products()
    else:
        raise ValueError(f"Unknown region: {region_id}")

    return RegionData(
        id=region_info["id"],
        name_ja=region_info["name_ja"],
        name_en=region_info["name_en"],
        mining_rates=region_info["mining_rates"],
        storage_limit=region_info["storage_limit"],
        products=products,
        outposts=data["outposts"],
        # Power buffer for map facilities (turrets, ziplines, transfer storage)
        # Read from region JSON, fallback to 0 if not specified
        power_buffer=region_info.get("power_buffer", 0.0),
        precipitation_acid_supply=region_info.get("mining_rates", {}).get("precipitation_acid", 0.0),
    )


def _build_valley4_products() -> list[Product]:
    """Build Valley IV product specifications from analysis data."""

    # Production rates: 30/min for 2-sec cycle, 6/min for 10-sec cycle
    # Resource consumption from valley4_analysis.md (per minute at full rate)

    products = [
        # Basic materials (power from opt_sample.md at 30/min)
        Product(
            id="origocrust", name_ja="結晶外殻", name_en="Origocrust",
            trade_value=1, production_rate=30.0,
            originium_ore=30.0, power_consumption=13.0,  # from opt_sample.md
        ),
        Product(
            id="amethyst_bottle", name_ja="紫晶製ボトル", name_en="Amethyst Bottle",
            trade_value=2, production_rate=30.0,
            amethyst_ore=60.0, power_consumption=20.0,  # from opt_sample.md
        ),
        Product(
            id="amethyst_part", name_ja="紫晶部品", name_en="Amethyst Part",
            trade_value=1, production_rate=30.0,
            amethyst_ore=30.0, power_consumption=25.0,  # from opt_sample.md
        ),
        Product(
            id="ferrium_part", name_ja="鉄製部品", name_en="Ferrium Part",
            trade_value=1, production_rate=30.0,
            ferrium_ore=30.0, power_consumption=40.0,  # from opt_sample.md
        ),
        Product(
            id="steel_part", name_ja="鋼製部品", name_en="Steel Part",
            trade_value=3, production_rate=30.0,
            ferrium_ore=60.0, power_consumption=80.0,  # from opt_sample.md
        ),

        # Capsules and Canned Foods (power from opt_sample.md)
        Product(
            id="buck_capsule_c", name_ja="蕎花カプセルI", name_en="Buck Capsule C",
            trade_value=10, production_rate=6.0,
            amethyst_ore=60.0, power_consumption=137.0,  # from opt_sample.md
        ),
        Product(
            id="buck_capsule_b", name_ja="蕎花カプセルII", name_en="Buck Capsule B",
            trade_value=27, production_rate=6.0,
            ferrium_ore=120.0, power_consumption=328.0,  # from opt_sample.md
        ),
        Product(
            id="buck_capsule_a", name_ja="蕎花カプセルIII", name_en="Buck Capsule A",
            trade_value=70, production_rate=6.0,
            ferrium_ore=240.0, power_consumption=412.0,  # from opt_sample.md
        ),
        Product(
            id="canned_citrome_c", name_ja="シトローム缶詰I", name_en="Canned Citrome C",
            trade_value=10, production_rate=6.0,
            amethyst_ore=60.0, power_consumption=137.0,  # from opt_sample.md
        ),
        Product(
            id="canned_citrome_b", name_ja="シトローム缶詰II", name_en="Canned Citrome B",
            trade_value=27, production_rate=6.0,
            ferrium_ore=120.0, power_consumption=328.0,  # from opt_sample.md
        ),
        Product(
            id="canned_citrome_a", name_ja="シトローム缶詰III", name_en="Canned Citrome A",
            trade_value=70, production_rate=6.0,
            ferrium_ore=240.0, power_consumption=412.0,  # from opt_sample.md
        ),

        # Batteries (power from opt_sample.md: HC 1030/2=515, SC 195, LC 78 at 6/min)
        Product(
            id="lc_valley_battery", name_ja="小容量谷地バッテリー", name_en="LC Valley Battery",
            trade_value=16, production_rate=6.0,
            originium_ore=60.0, amethyst_ore=30.0, power_consumption=78.0,  # from opt_sample.md
            is_battery=True, battery_power=166.67,  # 1000 power * 40 sec / 240 sec/min
        ),
        Product(
            id="sc_valley_battery", name_ja="中容量谷地バッテリー", name_en="SC Valley Battery",
            trade_value=30, production_rate=6.0,
            originium_ore=90.0, ferrium_ore=60.0, power_consumption=195.0,  # from opt_sample.md
            is_battery=True, battery_power=83.33,  # 500 power * 40 sec / 240 sec/min
        ),
        Product(
            id="hc_valley_battery", name_ja="大容量谷地バッテリー", name_en="HC Valley Battery",
            trade_value=70, production_rate=6.0,
            originium_ore=180.0, ferrium_ore=120.0, power_consumption=515.0,  # from opt_sample.md (1030/2)
            is_battery=True, battery_power=733.33,  # 1100 power * 40 sec / 60 sec/min
        ),
    ]

    return products


def _build_wuling_products() -> list[Product]:
    """Build Wuling v1.2 product specifications.

    Power and material consumption values are derived from verify_power.py
    chain calculations. Outpost assignment (sold_at) follows v1.2 wiki data.
    """

    products = [
        # Xiranite (息壌) - production limited by Forge of the Sky
        # v1.2: Forge of the Sky 8台 (initial) - 12台 (after Forge Expansion IV)
        # Conservative: 8台 = 240/min for v1.2 base case
        Product(
            id="xiranite", name_ja="息壌", name_en="Xiranite",
            trade_value=1, production_rate=30.0,
            power_consumption=77.5,
            production_limit=240.0,  # v1.2: 8 Forge of the Sky × 30/min
            sold_at=["tianwangyuan", "cardiac_remediation"],
        ),

        # Cuprium Part (赤銅部品) - v1.1
        Product(
            id="cuprium_part", name_ja="赤銅部品", name_en="Cuprium Part",
            trade_value=1, production_rate=30.0,
            cuprium_ore=30.0, power_consumption=25.0,
            sewage_production=30.0,  # 1 sewage per cuprium refined
            sold_at=["tianwangyuan"],
        ),

        # Jincao Drink (錦草ソーダ)
        Product(
            id="jincao_drink", name_ja="錦草ソーダ", name_en="Jincao Drink",
            trade_value=16, production_rate=6.0,
            ferrium_ore=120.0, power_consumption=175.0,
            sold_at=["tianwangyuan"],
        ),

        # Jincao Tea (錦草ソーダⅡ) - v1.1 既存だが v1.2 で取引対象に
        # Cuprium chain: 120 Cuprium/min → 120 Sewage byproduct
        # Power: chain (verify_power: ~272.5)
        Product(
            id="jincao_tea", name_ja="錦草ソーダⅡ", name_en="Jincao Tea",
            trade_value=22, production_rate=6.0,
            cuprium_ore=120.0, power_consumption=272.5,
            sewage_production=120.0,
            sold_at=["cardiac_remediation"],
        ),

        # Yazhen Syringe C (芽針注射剤I)
        Product(
            id="yazhen_syringe_c", name_ja="芽針注射剤I", name_en="Yazhen Syringe C",
            trade_value=16, production_rate=6.0,
            ferrium_ore=120.0, power_consumption=175.0,
            sold_at=["tianwangyuan"],
        ),

        # Yazhen Syringe A (芽針注射剤Ⅱ) - v1.1
        Product(
            id="yazhen_syringe_a", name_ja="芽針注射剤Ⅱ", name_en="Yazhen Syringe A",
            trade_value=22, production_rate=6.0,
            cuprium_ore=120.0, power_consumption=272.5,
            sewage_production=120.0,
            sold_at=["tianwangyuan", "cardiac_remediation"],
        ),

        # LC Wuling Battery
        Product(
            id="lc_wuling_battery", name_ja="小容量武陵バッテリー", name_en="LC Wuling Battery",
            trade_value=25, production_rate=6.0,
            originium_ore=180.0, power_consumption=227.5,
            xiranite_consumption=30.0,
            sandleaf_consumption=30.0,
            is_battery=True, battery_power=1066.67,
            sold_at=["tianwangyuan", "cardiac_remediation"],
        ),

        # SC Wuling Battery (中容量武陵バッテリー)
        Product(
            id="sc_wuling_battery", name_ja="中容量武陵バッテリー", name_en="SC Wuling Battery",
            trade_value=54, production_rate=6.0,
            originium_ore=240.0, ferrium_ore=30.0,
            power_consumption=681.67,
            xiranite_consumption=60.0,
            sandleaf_consumption=40.0,
            sewage_consumption=30.0,
            is_battery=True, battery_power=2133.33,
            sold_at=["tianwangyuan", "cardiac_remediation"],
        ),

        # === v1.2 NEW PRODUCTS ===

        # Heavy Xiranite (重息壌) - v1.2
        # 1台 Forge for Heavy + 3台 Forge for Xiranite (90/min) = 4台 Forge total
        # Xircon Effluent 30/min via Reactor: Liquid Xiranite + Sewage → XE + IXE
        # Sewage 30/min net consumption (must be from Cuprium products elsewhere)
        # Power chain: forge×4 (200) + reactor×2 (100) + refining×12 (60) + shredding×3 (15) + others ~40 = 415
        # No precipitation acid needed (basic recipe doesn't go through Liquid Heavy Xiranite)
        Product(
            id="heavy_xiranite", name_ja="重息壌", name_en="Heavy Xiranite",
            trade_value=27, production_rate=6.0,
            power_consumption=415.0,
            xiranite_consumption=90.0,  # 60 (Heavy) + 30 (for Liquid Xiranite → XE)
            sewage_consumption=30.0,    # net for Xircon Effluent reactor
            sold_at=["cardiac_remediation"],
        ),

        # Hetonite Part (緋銅部品) - v1.2
        # Chain: Cuprium ore→Cuprium→Powder→Solution(+PA)→HetoniteSolution(Purification, +PA byproduct)
        #        → Hetonite (+ Sewage byproduct) → Hetonite Part
        # Per 1 Hetonite Part: 30 PA pure consumption, 20 Cuprium ore, 5 Ferrium ore
        # Net Sewage produced: 20/individual (Cuprium refining)
        # Power: 835 unit/sec @ 6/min (verified)
        Product(
            id="hetonite_part", name_ja="緋銅部品", name_en="Hetonite Part",
            trade_value=48, production_rate=6.0,
            cuprium_ore=120.0, ferrium_ore=30.0,
            precipitation_acid=180.0,  # 30 PA/個 × 6/min net
            power_consumption=835.0,
            sewage_production=120.0,   # 20/個 × 6/min from Cuprium refining
            sold_at=["tianwangyuan"],
        ),

        # Xiranite Gourd (息壌ひょうたん) - v1.2 期間限定
        # Chain: Experimental Xiranite Bottle (Moulding 2s, Xiranite 2 → 1) [推定]
        #      + Experimental Xiranite Part (Fitting 2s, Xiranite 1 → 1) [確定]
        # Per 1 Gourd: 5 Bottle (= 10 Xiranite) + 5 Part (= 5 Xiranite) = 15 Xiranite
        # 6/min Gourd → 90 Xiranite/min (= Forge of the Sky 3台)
        # Power: 305 unit/sec @ 6/min (verified)
        Product(
            id="xiranite_gourd", name_ja="息壌ひょうたん", name_en="Xiranite Gourd",
            trade_value=40, production_rate=6.0,
            power_consumption=305.0,
            xiranite_consumption=90.0,  # 15 Xiranite × 6/min
            sold_at=["cardiac_remediation"],
            secondary_currency_value=10,  # 1 Gourd → 10 Fruits of Altruism Cert
        ),
    ]

    return products


# =============================================================================
# LP Formulation
# =============================================================================

def analyze_outpost_tickets(
    outposts: list[dict],
    ticket_rate: float,
    interval_hours: float,
    bonus_rate: float = 1.0,
) -> OutpostTicketAnalysis:
    """
    Analyze outpost ticket accumulation limits.

    Args:
        outposts: List of outpost data from region JSON
        ticket_rate: Production rate in tickets/min
        interval_hours: Sale interval in hours
        bonus_rate: Bonus multiplier for accumulation (e.g., 1.4 for +40%)

    Returns:
        OutpostTicketAnalysis with detailed breakdown
    """
    interval_minutes = interval_hours * 60
    produced_tickets = ticket_rate * interval_minutes

    total_accumulated = 0.0
    total_limit = 0.0
    outpost_details = []

    for outpost in outposts:
        rate_per_hour = outpost["ticket_rate"] * bonus_rate
        limit = outpost["ticket_max"]

        # Accumulation over interval (capped by limit)
        accumulated = min(rate_per_hour * interval_hours, limit)

        total_accumulated += accumulated
        total_limit += limit

        outpost_details.append({
            "id": outpost["id"],
            "name_ja": outpost["name_ja"],
            "rate_per_hour": rate_per_hour,
            "limit": limit,
            "accumulated": accumulated,
            "at_limit": accumulated >= limit,
            "hours_to_limit": limit / rate_per_hour if rate_per_hour > 0 else float("inf"),
        })

    available_tickets = min(total_accumulated, total_limit)
    effective_tickets = min(produced_tickets, available_tickets)
    effective_rate = effective_tickets / interval_minutes if interval_minutes > 0 else 0
    is_limited = produced_tickets > available_tickets
    limit_ratio = effective_tickets / produced_tickets if produced_tickets > 0 else 1.0

    return OutpostTicketAnalysis(
        total_accumulated=total_accumulated,
        total_limit=total_limit,
        available_tickets=available_tickets,
        produced_tickets=produced_tickets,
        effective_tickets=effective_tickets,
        effective_rate=effective_rate,
        is_limited=is_limited,
        limit_ratio=limit_ratio,
        outpost_details=outpost_details,
    )


@dataclass
class OutpostTicketAnalysis:
    """Analysis of outpost ticket accumulation limits."""
    total_accumulated: float  # tickets accumulated over interval
    total_limit: float  # sum of all outpost limits
    available_tickets: float  # min(accumulated, limit)
    produced_tickets: float  # tickets produced over interval
    effective_tickets: float  # min(produced, available)
    effective_rate: float  # effective tickets per minute
    is_limited: bool  # True if outpost limit constrains sales
    limit_ratio: float  # effective / produced (1.0 = no limitation)
    outpost_details: list[dict]  # per-outpost breakdown


@dataclass
class LPResult:
    """Result of the LP optimization."""
    success: bool
    message: str
    ticket_rate: float  # tickets per minute
    production_rates: dict[str, float]  # product_id -> production rate per minute
    ore_consumption: dict[str, float]  # ore_type -> consumption per minute
    power_consumption: float  # unit/sec
    power_supply: float  # unit/sec
    power_balance: float  # unit/sec
    battery_for_power: dict[str, float]  # battery_id -> rate used for power
    battery_for_sale: dict[str, float]  # battery_id -> rate for sale
    storage_analysis: dict[str, dict] = field(default_factory=dict)
    outpost_analysis: OutpostTicketAnalysis | None = None
    # v1.2: Multi-outpost sales allocation
    sales_by_outpost: dict[str, dict[str, float]] = field(default_factory=dict)  # outpost_id -> {product_id: rate}
    secondary_currency_rate: float = 0.0  # tickets/min of secondary currency (e.g. AIC certs)


def _is_sold_at(product: Product, outpost: dict) -> bool:
    """Check whether a product is sellable at an outpost."""
    if product.sold_at:
        return outpost["id"] in product.sold_at
    # Fallback: outpost's products list
    return product.id in outpost.get("products", [])


def solve_portfolio_multi_outpost(
    region: RegionData,
    min_interval_hours: float,
    machine_increment: float = 0.25,
    bonus_rate: float = 1.0,
    include_event_items: bool = True,
    cardiac_remediation_level: int = 2,
) -> LPResult:
    """
    Multi-outpost LP solver for v1.2 Wuling.

    Variables:
        q[i]:    production count for product i (integer, machine_increment unit)
        pw[b]:   power-allocation count for battery b (integer, 0.25 unit)
        s[i,j]:  sale rate of product i at outpost j (continuous, /min)

    Constraints:
        Mining:        Σi ore_i × p_i ≤ ore_rate
        PA:            Σi pa_i × p_i ≤ pa_supply
        Power:         Σi power_i × p_i + buffer ≤ Σb battery_power_b × pw_b
        Battery split: pw_b ≤ p_b
        Sale ≤ prod:   Σj s[i,j] + pw_b (if battery) ≤ p_i
        Outpost-only:  s[i,j] = 0 if product not sold at outpost j
        Xiranite:      production + consumption ≤ 240/min (Forge 8台)
        Sewage:        Σi (consumption - production) × p_i ≤ 0
        Storage:       s[i,j] × interval_min ≤ storage_limit
        Outpost cap:   Σi s[i,j] × price_i ≤ rate_j × bonus / 60   (per minute)
    Objective:
        max Σi Σj s[i,j] × price_i
    """
    products = list(region.products)
    if not include_event_items:
        products = [p for p in products if p.id != "xiranite_gourd"]

    # Adjust cardiac remediation level if specified
    outposts = []
    for o in region.outposts:
        o2 = dict(o)
        if o["id"] == "cardiac_remediation" and "level_table" in o:
            for lvl in o["level_table"]:
                if lvl["level"] == cardiac_remediation_level:
                    o2["ticket_rate"] = lvl["ticket_rate"]
                    o2["ticket_max"] = lvl["ticket_max"]
                    o2["level"] = cardiac_remediation_level
                    break
        outposts.append(o2)

    n = len(products)
    m = len(outposts)
    battery_indices = [i for i, p in enumerate(products) if p.is_battery]
    n_batteries = len(battery_indices)

    rate_increments = [p.production_rate * machine_increment for p in products]
    power_increment = 0.25
    power_rate_increments = [p.production_rate * power_increment for p in products]

    # Variable layout:
    n_q = n
    n_pw = n_batteries
    n_s = n * m
    n_vars = n_q + n_pw + n_s

    def q_idx(i: int) -> int:
        return i

    def pw_idx(bj: int) -> int:
        return n_q + bj

    def s_idx(i: int, j: int) -> int:
        return n_q + n_pw + i * m + j

    # Objective: maximize Σ s[i,j] × price (negate for minimization)
    c = np.zeros(n_vars)
    for i, p in enumerate(products):
        for j, o in enumerate(outposts):
            if _is_sold_at(p, o):
                c[s_idx(i, j)] = -p.trade_value

    A_ub = []
    b_ub = []
    A_eq = []
    b_eq = []

    # 1. Mining constraints
    ore_types = ["originium_ore", "amethyst_ore", "ferrium_ore", "cuprium_ore"]
    for ore_type in ore_types:
        rate = region.mining_rates.get(ore_type, 0)
        if rate > 0:
            row = np.zeros(n_vars)
            for i, p in enumerate(products):
                ore_per_rate = getattr(p, ore_type, 0.0) / p.production_rate
                row[q_idx(i)] = ore_per_rate * rate_increments[i]
            A_ub.append(row)
            b_ub.append(rate)

    # 2. Precipitation acid
    pa_supply = region.mining_rates.get("precipitation_acid", 0)
    if pa_supply > 0:
        row = np.zeros(n_vars)
        for i, p in enumerate(products):
            pa_per_rate = p.precipitation_acid / p.production_rate
            row[q_idx(i)] = pa_per_rate * rate_increments[i]
        A_ub.append(row)
        b_ub.append(pa_supply)

    # 3. Power balance
    row = np.zeros(n_vars)
    for i, p in enumerate(products):
        power_per_rate = p.power_consumption / p.production_rate
        row[q_idx(i)] = power_per_rate * rate_increments[i]
    for bj, bi in enumerate(battery_indices):
        bp = products[bi].battery_power
        row[pw_idx(bj)] = -bp * power_rate_increments[bi]
    A_ub.append(row)
    b_ub.append(-region.power_buffer)

    # 4. Battery: pw ≤ p (in increment units, pw_count × power_inc ≤ q_count × machine_inc)
    for bj, bi in enumerate(battery_indices):
        row = np.zeros(n_vars)
        row[pw_idx(bj)] = power_increment
        row[q_idx(bi)] = -machine_increment
        A_ub.append(row)
        b_ub.append(0)

    # 5. Sale ≤ production (per product i: Σj s_ij + pw_actual ≤ p_i)
    for i, p in enumerate(products):
        row = np.zeros(n_vars)
        for j in range(m):
            row[s_idx(i, j)] = 1
        row[q_idx(i)] = -rate_increments[i]
        if i in battery_indices:
            bj = battery_indices.index(i)
            row[pw_idx(bj)] = power_rate_increments[i]
        A_ub.append(row)
        b_ub.append(0)

    # 6. Force s_ij = 0 if product not sold at outpost
    for i, p in enumerate(products):
        for j, o in enumerate(outposts):
            if not _is_sold_at(p, o):
                row = np.zeros(n_vars)
                row[s_idx(i, j)] = 1
                A_eq.append(row)
                b_eq.append(0)

    # 7. Xiranite limit (production + consumption ≤ 240)
    xiranite_idx = next((i for i, p in enumerate(products) if p.id == "xiranite"), None)
    has_xiranite_consumers = any(p.xiranite_consumption > 0 for p in products)
    if xiranite_idx is not None and has_xiranite_consumers:
        xp = products[xiranite_idx]
        if xp.production_limit:
            row = np.zeros(n_vars)
            row[q_idx(xiranite_idx)] = rate_increments[xiranite_idx]
            for i, p in enumerate(products):
                if p.xiranite_consumption > 0:
                    xc_per_rate = p.xiranite_consumption / p.production_rate
                    row[q_idx(i)] += xc_per_rate * rate_increments[i]
            A_ub.append(row)
            b_ub.append(xp.production_limit)

    # 8. Sewage balance (consumption ≤ production)
    has_sewage = any(p.sewage_consumption > 0 or p.sewage_production > 0 for p in products)
    if has_sewage:
        row = np.zeros(n_vars)
        for i, p in enumerate(products):
            net = (p.sewage_consumption - p.sewage_production) / p.production_rate
            row[q_idx(i)] = net * rate_increments[i]
        A_ub.append(row)
        b_ub.append(0)

    # 9. Storage cap per (product, outpost)
    interval_minutes = min_interval_hours * 60
    max_sale_rate = region.storage_limit / interval_minutes
    for i in range(n):
        for j in range(m):
            row = np.zeros(n_vars)
            row[s_idx(i, j)] = 1
            A_ub.append(row)
            b_ub.append(max_sale_rate)

    # 10. Outpost ticket accumulation cap
    for j, o in enumerate(outposts):
        rate_per_h = o.get("ticket_rate", 0) * bonus_rate
        if rate_per_h > 0:
            row = np.zeros(n_vars)
            for i, p in enumerate(products):
                if _is_sold_at(p, o):
                    row[s_idx(i, j)] = p.trade_value
            A_ub.append(row)
            b_ub.append(rate_per_h / 60)  # /min

    # Bounds
    lower = np.zeros(n_vars)
    upper = np.full(n_vars, np.inf)
    for i, p in enumerate(products):
        if p.production_limit is not None:
            upper[q_idx(i)] = p.production_limit / rate_increments[i]
        else:
            upper[q_idx(i)] = 10000
    for bj, bi in enumerate(battery_indices):
        upper[pw_idx(bj)] = upper[q_idx(bi)] * machine_increment / power_increment

    # Convert
    A_ub_arr = np.array(A_ub) if A_ub else np.zeros((0, n_vars))
    b_ub_arr = np.array(b_ub) if b_ub else np.zeros(0)
    A_eq_arr = np.array(A_eq) if A_eq else np.zeros((0, n_vars))
    b_eq_arr = np.array(b_eq) if b_eq else np.zeros(0)

    # MILP integrality: q & pw integer, s continuous
    integrality = np.zeros(n_vars, dtype=int)
    integrality[:n_q] = 1
    integrality[n_q:n_q + n_pw] = 1

    constraints = [LinearConstraint(A_ub_arr, -np.inf, b_ub_arr)]
    if len(A_eq) > 0:
        constraints.append(LinearConstraint(A_eq_arr, b_eq_arr, b_eq_arr))

    bounds_milp = Bounds(lower, upper)
    result = milp(c, constraints=constraints, bounds=bounds_milp, integrality=integrality)

    if not result.success:
        return LPResult(
            success=False, message=str(getattr(result, "message", "MILP failed")),
            ticket_rate=0, production_rates={}, ore_consumption={},
            power_consumption=0, power_supply=0, power_balance=0,
            battery_for_power={}, battery_for_sale={},
        )

    x = result.x

    # Decode
    production_rates = {}
    sales_by_outpost = {o["id"]: {} for o in outposts}
    for i, p in enumerate(products):
        prod = x[q_idx(i)] * rate_increments[i]
        if prod > 1e-6:
            production_rates[p.id] = prod
        for j, o in enumerate(outposts):
            sale = x[s_idx(i, j)]
            if sale > 1e-6:
                sales_by_outpost[o["id"]][p.id] = sale

    battery_for_power = {}
    battery_for_sale = {}
    for bj, bi in enumerate(battery_indices):
        p = products[bi]
        prod = x[q_idx(bi)] * rate_increments[bi]
        pw = x[pw_idx(bj)] * power_rate_increments[bi]
        if prod > 1e-6:
            battery_for_power[p.id] = pw
            battery_for_sale[p.id] = prod - pw

    total_ticket_rate = sum(
        x[s_idx(i, j)] * products[i].trade_value
        for i in range(n) for j in range(m)
    )
    secondary_currency = sum(
        x[s_idx(i, j)] * products[i].secondary_currency_value
        for i in range(n) for j in range(m)
        if products[i].secondary_currency_value > 0
    )

    # Mining/PA totals
    ore_consumption = {}
    for ore_type in ore_types:
        total = sum(
            x[q_idx(i)] * rate_increments[i] * (getattr(p, ore_type, 0.0) / p.production_rate)
            for i, p in enumerate(products)
        )
        if total > 1e-6:
            ore_consumption[ore_type] = total
    pa_total = sum(
        x[q_idx(i)] * rate_increments[i] * (p.precipitation_acid / p.production_rate)
        for i, p in enumerate(products)
    )
    if pa_total > 1e-6:
        ore_consumption["precipitation_acid"] = pa_total

    # Power
    power_consumption = sum(
        x[q_idx(i)] * rate_increments[i] * (p.power_consumption / p.production_rate)
        for i, p in enumerate(products)
    )
    power_supply = sum(
        x[pw_idx(bj)] * power_rate_increments[bi] * products[bi].battery_power
        for bj, bi in enumerate(battery_indices)
    )

    # Storage analysis (per outpost x product)
    storage_analysis = {}
    for o in outposts:
        for prod_id, sale_rate in sales_by_outpost[o["id"]].items():
            production = sale_rate * interval_minutes
            loss = max(0, production - region.storage_limit)
            storage_analysis[f"{prod_id}@{o['id']}"] = {
                "production": production,
                "storage_loss": loss,
                "effective": min(production, region.storage_limit),
                "loss_percent": loss / production * 100 if production > 0 else 0,
            }

    return LPResult(
        success=True,
        message="Optimal solution found",
        ticket_rate=total_ticket_rate,
        production_rates=production_rates,
        ore_consumption=ore_consumption,
        power_consumption=power_consumption,
        power_supply=power_supply,
        power_balance=power_supply - power_consumption - region.power_buffer,
        battery_for_power=battery_for_power,
        battery_for_sale=battery_for_sale,
        storage_analysis=storage_analysis,
        sales_by_outpost=sales_by_outpost,
        secondary_currency_rate=secondary_currency,
    )


def solve_portfolio(
    region: RegionData,
    min_interval_hours: float,
    use_machine_increments: bool = True,
    machine_increment: float = 0.25,
    bonus_rate: float = 1.0,
    include_event_items: bool = True,
) -> LPResult:
    """
    Solve the production portfolio optimization problem using MILP.

    The problem is:
        Maximize: sum(sale_rate_i * price_i) for all products i

    Subject to:
        1. Mining rate constraints:
           sum(production_rate_i * ore_consumption_i) <= mining_rate for each ore

        2. Power balance:
           sum(production_rate_i * power_i) + power_buffer <= sum(battery_power_rate_j * battery_power_j)

        3. Battery split constraint:
           For each battery type: production_rate = power_rate + sale_rate

        4. Intermediate material balance (e.g., xiranite):
           production >= sales + consumption_by_other_products

        5. Non-negativity: all rates >= 0

        6. Machine increment constraint (MILP):
           production_rate must be a multiple of (base_rate * machine_increment)

    Decision variables:
        - production_rate for each non-battery product (or sale_rate for intermediates like xiranite)
        - production_rate for each battery product
        - power_rate for each battery (how much goes to power)

    Args:
        region: Region data with products and constraints
        min_interval_hours: Minimum trade interval in hours
        use_machine_increments: If True, use MILP with 0.25 machine increments
        machine_increment: Machine count increment (default 0.25)
    """

    products = region.products
    n_products = len(products)

    # Identify batteries and intermediates (xiranite)
    battery_indices = [i for i, p in enumerate(products) if p.is_battery]
    xiranite_idx = next((i for i, p in enumerate(products) if p.id == "xiranite"), None)
    n_batteries = len(battery_indices)

    # Check if any product consumes xiranite
    has_xiranite_consumers = any(p.xiranite_consumption > 0 for p in products)

    # Calculate rate increments for each product based on machine_increment
    # rate_increment = production_rate_per_machine * machine_increment
    rate_increments = [p.production_rate * machine_increment for p in products]

    # Decision variable layout:
    # [prod_rate_0, ..., prod_rate_n-1, power_rate_bat0, ..., power_rate_bat_k-1]
    # For xiranite: the variable represents SALE rate, not total production
    # Total xiranite production = sale_rate + consumption_by_batteries

    n_vars = n_products + n_batteries

    # Build objective function (maximize ticket rate = minimize negative)
    c = np.zeros(n_vars)
    for i, p in enumerate(products):
        c[i] = -p.trade_value  # negative because we minimize

    # For batteries, subtract the power rate contribution (power batteries don't generate tickets)
    for j, bat_idx in enumerate(battery_indices):
        power_var_idx = n_products + j
        c[power_var_idx] = products[bat_idx].trade_value  # positive (reduces objective)

    # Inequality constraints: A_ub @ x <= b_ub
    A_ub = []
    b_ub = []

    # 1. Mining rate constraints
    # sum(prod_rate_i * ore_per_unit_rate_i) <= mining_rate
    ore_types = ["originium_ore", "amethyst_ore", "ferrium_ore", "cuprium_ore"]
    for ore_type in ore_types:
        mining_rate = region.mining_rates.get(ore_type, 0)
        if mining_rate > 0:
            row = np.zeros(n_vars)
            for i, p in enumerate(products):
                ore_per_rate = getattr(p, ore_type, 0.0) / p.production_rate if p.production_rate > 0 else 0
                row[i] = ore_per_rate
            A_ub.append(row)
            b_ub.append(mining_rate)

    # 2. Power balance constraint
    # sum(prod_rate_i * power_i / prod_rate) + buffer <= sum(power_rate_j * battery_power_j)
    # Note: For products that consume xiranite (like LC Wuling Battery), the power_consumption
    # already includes xiranite production power, so we don't add it separately.
    # However, if xiranite is sold directly, we need to add its power.
    row = np.zeros(n_vars)
    for i, p in enumerate(products):
        power_per_rate = p.power_consumption / p.production_rate if p.production_rate > 0 else 0
        row[i] = power_per_rate

    for j, bat_idx in enumerate(battery_indices):
        power_var_idx = n_products + j
        row[power_var_idx] = -products[bat_idx].battery_power

    # If xiranite is sold (as its own product), add its power consumption
    # This is for the case where xiranite_sales > 0
    if xiranite_idx is not None:
        xiranite_product = products[xiranite_idx]
        xiranite_power_per_rate = xiranite_product.power_consumption / xiranite_product.production_rate
        row[xiranite_idx] = xiranite_power_per_rate

    A_ub.append(row)
    b_ub.append(-region.power_buffer)  # We need power_supply >= consumption + buffer

    # 3. Power rate cannot exceed production rate for each battery
    # power_rate_j <= prod_rate_bat_j
    for j, bat_idx in enumerate(battery_indices):
        row = np.zeros(n_vars)
        row[bat_idx] = -1  # -prod_rate
        row[n_products + j] = 1  # +power_rate
        A_ub.append(row)
        b_ub.append(0)

    # 4. Xiranite production limit constraint (if applicable)
    # For products consuming xiranite: xiranite_sale + sum(consumption) <= xiranite_production_limit
    # This is already handled by the production_limit on xiranite, but we need to account for
    # the fact that xiranite_sale + xiranite_consumed <= limit
    if xiranite_idx is not None and has_xiranite_consumers:
        xiranite_product = products[xiranite_idx]
        if xiranite_product.production_limit is not None:
            row = np.zeros(n_vars)
            row[xiranite_idx] = 1  # xiranite sales
            for i, p in enumerate(products):
                if p.xiranite_consumption > 0:
                    xiranite_per_rate = p.xiranite_consumption / p.production_rate
                    row[i] += xiranite_per_rate
            A_ub.append(row)
            b_ub.append(xiranite_product.production_limit)

    # 5. Sewage balance constraint
    # sum(sewage_consumption_i * rate_i / prod_rate_i) <= sum(sewage_production_i * rate_i / prod_rate_i)
    # SC Battery needs sewage from Cuprium refining byproducts of other products
    has_sewage = any(p.sewage_consumption > 0 or p.sewage_production > 0 for p in products)
    if has_sewage:
        row = np.zeros(n_vars)
        for i, p in enumerate(products):
            net = (p.sewage_consumption - p.sewage_production) / p.production_rate if p.production_rate > 0 else 0
            row[i] = net
        A_ub.append(row)
        b_ub.append(0)

    # 6. Storage limit constraints
    # For each non-battery product: sale_rate * interval_minutes <= storage_limit
    # For batteries: (prod_rate - power_rate) * interval_minutes <= storage_limit
    interval_minutes = min_interval_hours * 60
    max_sale_rate = region.storage_limit / interval_minutes

    for i, p in enumerate(products):
        if p.is_battery:
            # Battery: (prod_rate - power_rate) <= max_sale_rate
            # => prod_rate - power_rate <= max_sale_rate
            # We need to find which power_var corresponds to this battery
            bat_j = battery_indices.index(i)
            row = np.zeros(n_vars)
            row[i] = 1  # production rate
            row[n_products + bat_j] = -1  # minus power rate = sale rate
            A_ub.append(row)
            b_ub.append(max_sale_rate)
        else:
            # Non-battery: just bound on production rate (handled in bounds below)
            pass

    # Bounds
    lower_bounds = np.zeros(n_vars)
    upper_bounds = np.full(n_vars, np.inf)

    for i, p in enumerate(products):
        if p.id == "xiranite" and has_xiranite_consumers:
            # For xiranite with consumers, production_limit is handled by constraint above.
            # But storage limit still applies to the sales rate variable.
            upper_bounds[i] = max_sale_rate
        elif p.is_battery:
            # Battery bounds: production can be higher than sale (some goes to power)
            if p.production_limit is not None:
                upper_bounds[i] = p.production_limit
        else:
            # Non-battery: sale rate = production rate, limited by storage
            upper_storage = max_sale_rate
            upper_limit = p.production_limit if p.production_limit is not None else np.inf
            upper_bounds[i] = min(upper_storage, upper_limit)

    # Convert to arrays
    A_ub = np.array(A_ub) if A_ub else np.zeros((0, n_vars))
    b_ub = np.array(b_ub) if b_ub else np.zeros(0)

    # Solve using MILP or LP
    if use_machine_increments:
        # Use MILP with integer variables for machine counts
        # Transform: x_i (production rate) = q_i * rate_increment_i
        # where q_i is a non-negative integer (quarter-machine count)

        # New decision variables: [q_0, ..., q_{n-1}, qp_0, ..., qp_{k-1}]
        # where q_i = quarter-machine count for product i
        # and qp_j = quarter-machine count for power allocation of battery j

        # Power allocation is always in 0.25 increments (1 generator = 0.25 production machine)
        # This is independent of the production machine increment
        power_increment = 0.25
        power_rate_increments = [p.production_rate * power_increment for p in products]

        # Transform objective: c'[i] = c[i] * rate_increment[i]
        c_milp = np.zeros(n_vars)
        for i in range(n_products):
            c_milp[i] = c[i] * rate_increments[i]
        for j, bat_idx in enumerate(battery_indices):
            # Power rate increment is always 0.25 (generator granularity)
            c_milp[n_products + j] = c[n_products + j] * power_rate_increments[bat_idx]

        # Transform constraints: A_ub_milp[i] = A_ub[i] * rate_increment
        A_ub_milp = np.zeros_like(A_ub)
        for row_idx in range(len(A_ub)):
            for i in range(n_products):
                A_ub_milp[row_idx, i] = A_ub[row_idx, i] * rate_increments[i]
            for j, bat_idx in enumerate(battery_indices):
                # Power allocation always uses 0.25 increment
                A_ub_milp[row_idx, n_products + j] = A_ub[row_idx, n_products + j] * power_rate_increments[bat_idx]

        # Transform bounds
        lower_bounds_milp = np.zeros(n_vars)
        upper_bounds_milp = np.zeros(n_vars)
        for i in range(n_products):
            lower_bounds_milp[i] = 0
            if np.isinf(upper_bounds[i]):
                upper_bounds_milp[i] = 10000  # Large upper bound for integers
            else:
                # Use floor to ensure we don't exceed storage limits
                upper_bounds_milp[i] = np.floor(upper_bounds[i] / rate_increments[i])
        for j, bat_idx in enumerate(battery_indices):
            lower_bounds_milp[n_products + j] = 0
            # Power upper bound: production (in production increments) converted to power increments
            # power_rate <= production_rate
            # power_units * power_increment <= prod_units * machine_increment
            # power_units <= prod_units * machine_increment / power_increment
            upper_bounds_milp[n_products + j] = upper_bounds_milp[bat_idx] * machine_increment / power_increment

        # All variables are integers
        integrality = np.ones(n_vars, dtype=int)

        # Use scipy.optimize.milp
        constraints = LinearConstraint(A_ub_milp, -np.inf, b_ub)
        bounds_milp = Bounds(lower_bounds_milp, upper_bounds_milp)

        result = milp(
            c_milp,
            constraints=constraints,
            bounds=bounds_milp,
            integrality=integrality,
        )

        # Transform solution back to rates
        if result.success:
            x = np.zeros(n_vars)
            for i in range(n_products):
                x[i] = result.x[i] * rate_increments[i]
            for j, bat_idx in enumerate(battery_indices):
                # Power allocation uses 0.25 increment
                x[n_products + j] = result.x[n_products + j] * power_rate_increments[bat_idx]
        else:
            x = None
    else:
        # Use standard LP (continuous variables)
        bounds = [(lower_bounds[i], upper_bounds[i] if not np.isinf(upper_bounds[i]) else None)
                  for i in range(n_vars)]

        result = linprog(
            c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs"
        )
        x = result.x if result.success else None

    if not result.success or x is None:
        return LPResult(
            success=False,
            message=result.message if hasattr(result, 'message') else "Optimization failed",
            ticket_rate=0,
            production_rates={},
            ore_consumption={},
            power_consumption=0,
            power_supply=0,
            power_balance=0,
            battery_for_power={},
            battery_for_sale={},
        )

    # Extract solution
    production_rates = {}
    for i, p in enumerate(products):
        if x[i] > 1e-6:
            production_rates[p.id] = x[i]

    # Battery allocation
    battery_for_power = {}
    battery_for_sale = {}
    for j, bat_idx in enumerate(battery_indices):
        p = products[bat_idx]
        prod_rate = x[bat_idx]
        power_rate = x[n_products + j]
        if prod_rate > 1e-6:
            battery_for_power[p.id] = power_rate
            battery_for_sale[p.id] = prod_rate - power_rate

    # Calculate totals
    total_ticket_rate = -result.fun

    ore_consumption = {}
    for ore_type in ore_types:
        total = 0.0
        for i, p in enumerate(products):
            ore_per_rate = getattr(p, ore_type, 0.0) / p.production_rate if p.production_rate > 0 else 0
            total += x[i] * ore_per_rate
        if total > 1e-6:
            ore_consumption[ore_type] = total

    power_consumption = 0.0
    for i, p in enumerate(products):
        power_per_rate = p.power_consumption / p.production_rate if p.production_rate > 0 else 0
        power_consumption += x[i] * power_per_rate
        # Note: For products consuming xiranite, the power_consumption already includes
        # xiranite production, so we don't add it separately here.

    power_supply = 0.0
    for j, bat_idx in enumerate(battery_indices):
        power_rate = x[n_products + j]
        power_supply += power_rate * products[bat_idx].battery_power

    # Storage analysis for given interval
    interval_minutes = min_interval_hours * 60
    storage_analysis = {}
    for i, p in enumerate(products):
        if x[i] > 1e-6:
            rate = x[i]
            # For batteries, only the sale portion counts for storage
            if p.is_battery and p.id in battery_for_sale:
                rate = battery_for_sale[p.id]

            production = rate * interval_minutes
            storage_loss = max(0, production - region.storage_limit)
            storage_analysis[p.id] = {
                "production": production,
                "storage_loss": storage_loss,
                "effective": min(production, region.storage_limit),
                "loss_percent": storage_loss / production * 100 if production > 0 else 0,
            }

    # Analyze outpost ticket limits
    outpost_analysis = analyze_outpost_tickets(
        region.outposts,
        total_ticket_rate,
        min_interval_hours,
        bonus_rate=1.0,  # No bonus assumed; user can check with bonus separately
    )

    return LPResult(
        success=True,
        message="Optimal solution found",
        ticket_rate=total_ticket_rate,
        production_rates=production_rates,
        ore_consumption=ore_consumption,
        power_consumption=power_consumption,
        power_supply=power_supply,
        power_balance=power_supply - power_consumption - region.power_buffer,
        battery_for_power=battery_for_power,
        battery_for_sale=battery_for_sale,
        storage_analysis=storage_analysis,
        outpost_analysis=outpost_analysis,
    )


# =============================================================================
# Output Formatting
# =============================================================================

def format_output(region: RegionData, result: LPResult, interval_hours: float) -> str:
    """Format the optimization result in markdown."""

    lines = []
    lines.append(f"# {region.name_en} ({region.name_ja}) - Optimal Portfolio")
    lines.append("")
    lines.append(f"## Sale Interval: {interval_hours}h")
    lines.append("")

    if not result.success:
        lines.append(f"**Optimization failed**: {result.message}")
        return "\n".join(lines)

    # Production table
    lines.append("## Production Table")
    lines.append("")
    # Determine which ore types are relevant for this region
    ore_display = []
    ore_attr_map = {
        "originium_ore": ("Originium", "源石鉱"),
        "amethyst_ore": ("Amethyst", "紫晶鉱"),
        "ferrium_ore": ("Ferrium", "青鉄鉱"),
        "cuprium_ore": ("Cuprium", "赤銅鉱"),
    }
    for ore_type, (en_name, _ja_name) in ore_attr_map.items():
        if region.mining_rates.get(ore_type, 0) > 0 or any(
            getattr(p, ore_type, 0) > 0 for p in region.products
        ):
            ore_display.append((ore_type, en_name))

    ore_headers = " | ".join(name for _, name in ore_display)
    ore_separators = " | ".join("---" for _ in ore_display)
    lines.append(f"| Product | Machines | Rate (/min) | {ore_headers} | Power (unit/sec) | Price |")
    lines.append(f"|---------|----------|------------|{ore_separators}|------------------|-------|")

    products_by_id = {p.id: p for p in region.products}

    ore_totals = {ore_type: 0.0 for ore_type, _ in ore_display}
    total_power = 0.0
    total_machines = 0.0

    for prod_id, rate in sorted(result.production_rates.items()):
        p = products_by_id[prod_id]
        scale = rate / p.production_rate
        machines = scale  # machine count = rate / rate_per_machine

        power = p.power_consumption * scale
        total_power += power
        total_machines += machines

        ore_values = []
        for ore_type, _ in ore_display:
            val = getattr(p, ore_type, 0.0) * scale
            ore_totals[ore_type] += val
            ore_values.append(f"{val:.0f}" if val > 0 else "-")

        ore_cells = " | ".join(ore_values)
        lines.append(f"| {p.name_en} | {machines:.2f} | {rate:.2f} | {ore_cells} | {power:.0f} | {p.trade_value} |")

    # Totals row
    ore_total_strs = []
    for ore_type, _ in ore_display:
        total = ore_totals[ore_type]
        surplus = region.mining_rates.get(ore_type, 0) - total
        ore_total_strs.append(f"**{total:.0f}** (surplus {surplus:.0f})")
    ore_total_cells = " | ".join(ore_total_strs)

    lines.append(f"| **Total** | **{total_machines:.2f}** | | {ore_total_cells} | **{total_power:.0f}** | |")
    lines.append("")

    # Power allocation
    lines.append("## Power Allocation")
    lines.append("")
    lines.append("| Battery | Production | For Power | For Sale |")
    lines.append("|---------|------------|-----------|----------|")

    for bat_id in result.battery_for_power.keys():
        p = products_by_id[bat_id]
        prod_rate = result.production_rates.get(bat_id, 0)
        power_rate = result.battery_for_power.get(bat_id, 0)
        sale_rate = result.battery_for_sale.get(bat_id, 0)
        lines.append(f"| {p.name_en} | {prod_rate:.2f}/min | {power_rate:.2f}/min | {sale_rate:.2f}/min |")

    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|------|-------|")
    lines.append(f"| **Ticket Rate** | **{result.ticket_rate:.2f} tickets/min** |")
    lines.append(f"| Power Supply | {result.power_supply:.0f} unit/sec |")
    lines.append(f"| Power Consumption | {result.power_consumption:.0f} unit/sec |")
    lines.append(f"| Power Buffer | {region.power_buffer:.0f} unit/sec |")
    lines.append(f"| **Power Balance** | **{result.power_balance:+.0f} unit/sec** |")
    lines.append("")

    # Ticket breakdown
    lines.append("## Ticket Breakdown")
    lines.append("")
    lines.append("| Product | Sale Rate | Price | Tickets/min |")
    lines.append("|---------|-----------|-------|-------------|")

    total_tickets = 0.0
    for prod_id, rate in sorted(result.production_rates.items()):
        p = products_by_id[prod_id]

        # For batteries, use sale rate
        if p.is_battery:
            sale_rate = result.battery_for_sale.get(prod_id, 0)
        else:
            sale_rate = rate

        if sale_rate > 1e-6:
            tickets = sale_rate * p.trade_value
            total_tickets += tickets
            lines.append(f"| {p.name_en} | {sale_rate:.2f} | {p.trade_value} | {tickets:.2f} |")

    lines.append(f"| **Total** | | | **{total_tickets:.2f}** |")
    lines.append("")

    # Storage analysis
    lines.append(f"## Storage Analysis ({interval_hours}h interval)")
    lines.append("")
    lines.append("| Product | Production | Storage Limit | Loss | Loss % |")
    lines.append("|---------|------------|---------------|------|--------|")

    total_loss_value = 0.0
    for key, analysis in result.storage_analysis.items():
        # v1.2 multi-outpost: keys may be "<product_id>@<outpost_id>"
        prod_id = key.split("@", 1)[0]
        outpost_suffix = ""
        if "@" in key:
            outpost_suffix = f" @ {key.split('@', 1)[1]}"
        p = products_by_id.get(prod_id)
        if not p:
            continue
        loss_value = analysis["storage_loss"] * p.trade_value
        total_loss_value += loss_value

        loss_str = f"{analysis['storage_loss']:.0f}" if analysis["storage_loss"] > 0 else "-"
        loss_pct_str = f"{analysis['loss_percent']:.1f}%" if analysis["loss_percent"] > 0 else "-"

        lines.append(f"| {p.name_en}{outpost_suffix} | {analysis['production']:.0f} | {region.storage_limit} | {loss_str} | {loss_pct_str} |")

    if total_loss_value > 0:
        lines.append(f"| **Total Loss Value** | | | **{total_loss_value:.0f} tickets** | |")

    lines.append("")

    # Effective rate after storage loss
    interval_minutes = interval_hours * 60
    produced_tickets = result.ticket_rate * interval_minutes
    effective_tickets = produced_tickets - total_loss_value
    effective_rate = effective_tickets / interval_minutes

    lines.append("## Effective Rate (Storage)")
    lines.append("")
    lines.append(f"| Interval | Production | Storage Loss | Effective | Effective Rate |")
    lines.append(f"|----------|------------|--------------|-----------|----------------|")
    lines.append(f"| {interval_hours}h | {produced_tickets:.0f} | {total_loss_value:.0f} | {effective_tickets:.0f} | **{effective_rate:.2f}/min** |")
    lines.append("")

    # Outpost ticket analysis
    if result.outpost_analysis:
        oa = result.outpost_analysis
        lines.append("## Outpost Ticket Analysis")
        lines.append("")
        lines.append("| Outpost | Rate (/h) | Limit | Accumulated | At Limit? |")
        lines.append("|---------|-----------|-------|-------------|-----------|")

        for detail in oa.outpost_details:
            at_limit_str = "⚠️ Yes" if detail["at_limit"] else "No"
            lines.append(f"| {detail['name_ja']} | {detail['rate_per_hour']:.0f} | {detail['limit']:,} | {detail['accumulated']:,.0f} | {at_limit_str} |")

        lines.append(f"| **Total** | | **{oa.total_limit:,.0f}** | **{oa.available_tickets:,.0f}** | |")
        lines.append("")

        # Warning if limited
        if oa.is_limited:
            lines.append("### ⚠️ WARNING: Outpost Ticket Limit Reached")
            lines.append("")
            lines.append(f"Production ({oa.produced_tickets:,.0f} tickets) exceeds available outpost tickets ({oa.available_tickets:,.0f}).")
            lines.append("")
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Theoretical Rate | {result.ticket_rate:.2f}/min |")
            lines.append(f"| **Effective Rate (Outpost Limited)** | **{oa.effective_rate:.2f}/min** |")
            lines.append(f"| Efficiency Loss | {(1 - oa.limit_ratio) * 100:.1f}% |")
            lines.append("")
            lines.append("Consider shorter sale intervals or applying defense mission bonuses (+40% for Valley IV, +30% for Wuling).")
            lines.append("")
        else:
            lines.append(f"✅ Outpost capacity sufficient: {oa.available_tickets:,.0f} available vs {oa.produced_tickets:,.0f} produced")
            lines.append("")

    # v1.2: Multi-outpost sales breakdown
    if result.sales_by_outpost:
        lines.append("## Sales by Outpost (v1.2 multi-outpost)")
        lines.append("")
        for outpost in region.outposts:
            ot_id = outpost["id"]
            sales = result.sales_by_outpost.get(ot_id, {})
            if not sales:
                continue
            lines.append(f"### {outpost['name_ja']} ({ot_id})")
            lines.append("")
            lines.append("| Product | Sale (/min) | Price | Tickets/min |")
            lines.append("|---------|-------------|-------|-------------|")
            outpost_total = 0.0
            for prod_id, sale_rate in sorted(sales.items(), key=lambda kv: -kv[1] * products_by_id[kv[0]].trade_value):
                p = products_by_id[prod_id]
                tickets = sale_rate * p.trade_value
                outpost_total += tickets
                lines.append(f"| {p.name_ja} | {sale_rate:.2f} | {p.trade_value} | {tickets:.2f} |")
            lines.append(f"| **小計** | | | **{outpost_total:.2f}** |")
            # Compare with outpost cap
            rate_per_h = outpost.get("ticket_rate", 0)
            cap_per_min = rate_per_h / 60
            util = outpost_total / cap_per_min * 100 if cap_per_min > 0 else 0
            lines.append(f"")
            lines.append(f"蓄積率: {rate_per_h:,.0f}/h ({cap_per_min:.2f}/min) — 利用率 **{util:.1f}%**")
            lines.append("")

        if result.secondary_currency_rate > 0:
            lines.append(f"**支援成果券レート**: {result.secondary_currency_rate:.2f}/min "
                         f"({result.secondary_currency_rate * 60:.0f}/h)")
            lines.append("")

    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Solve Endfield production portfolio optimization"
    )
    parser.add_argument(
        "region",
        help="Region ID (valley_iv, wuling)",
    )
    parser.add_argument(
        "interval",
        type=float,
        help="Minimum trade interval in hours",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    parser.add_argument(
        "--power-buffer",
        type=float,
        default=None,
        help="Override default power buffer (unit/sec)",
    )
    parser.add_argument(
        "-i", "--increment",
        type=int,
        choices=[1, 2, 3, 4],
        default=4,
        help="Machine increment divisor: 1=integer, 2=0.5, 3=0.333, 4=0.25 (default: 4)",
    )
    parser.add_argument(
        "--bonus",
        type=float,
        default=1.30,
        help="Outpost accumulation bonus multiplier (default: 1.30 for +30%%)",
    )
    parser.add_argument(
        "--no-gourd",
        action="store_true",
        help="Exclude Xiranite Gourd (event-limited item) from optimization",
    )
    parser.add_argument(
        "--cardiac-level",
        type=int,
        choices=[1, 2],
        default=2,
        help="Cardiac Remediation Station level (Wuling only, default: 2)",
    )

    args = parser.parse_args()

    # Find base path (assumes script is in scripts/ subdirectory)
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent

    try:
        region = load_region_data(args.region, base_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading region data: {e}", file=sys.stderr)
        sys.exit(1)

    # Override power buffer if specified
    if args.power_buffer is not None:
        region.power_buffer = args.power_buffer

    # Calculate machine increment from CLI argument
    machine_increment = 1.0 / args.increment

    # Use multi-outpost solver for Wuling, legacy single-outpost for Valley IV
    if args.region.lower() == "wuling":
        result = solve_portfolio_multi_outpost(
            region, args.interval,
            machine_increment=machine_increment,
            bonus_rate=args.bonus,
            include_event_items=not args.no_gourd,
            cardiac_remediation_level=args.cardiac_level,
        )
    else:
        result = solve_portfolio(region, args.interval, machine_increment=machine_increment)

    if args.json:
        outpost_data = None
        if result.outpost_analysis:
            oa = result.outpost_analysis
            outpost_data = {
                "total_accumulated": oa.total_accumulated,
                "total_limit": oa.total_limit,
                "available_tickets": oa.available_tickets,
                "produced_tickets": oa.produced_tickets,
                "effective_tickets": oa.effective_tickets,
                "effective_rate": oa.effective_rate,
                "is_limited": oa.is_limited,
                "limit_ratio": oa.limit_ratio,
                "outpost_details": oa.outpost_details,
            }
        output = {
            "success": result.success,
            "message": result.message,
            "ticket_rate": result.ticket_rate,
            "production_rates": result.production_rates,
            "ore_consumption": result.ore_consumption,
            "power_consumption": result.power_consumption,
            "power_supply": result.power_supply,
            "power_balance": result.power_balance,
            "battery_for_power": result.battery_for_power,
            "battery_for_sale": result.battery_for_sale,
            "storage_analysis": result.storage_analysis,
            "outpost_analysis": outpost_data,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_output(region, result, args.interval))


if __name__ == "__main__":
    main()
