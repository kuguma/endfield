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
from scipy.optimize import linprog, OptimizeResult


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
    power_consumption: float = 0.0  # unit/sec at production_rate
    production_limit: float | None = None  # max production rate if limited
    is_battery: bool = False
    battery_power: float = 0.0  # power output per battery (unit/sec)
    # Intermediate material requirements (for Wuling)
    xiranite_consumption: float = 0.0  # xiranite consumed per minute at production_rate
    sandleaf_consumption: float = 0.0  # sandleaf consumed per minute at production_rate


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
        # Valley IV: 5 maps × (12 turrets × 20 + 30 ziplines × 5) ≈ 2000 unit/sec
        # Wuling: 2 maps but documented solution shows no buffer, so we set to 0 for now
        power_buffer=2000.0 if region_id.lower() in ("valley_iv", "valley4") else 0.0,
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
    """Build Wuling product specifications from analysis data."""

    products = [
        # Xiranite (息壌) - production limited to 60/min by Forge of the Sky
        Product(
            id="xiranite", name_ja="息壌", name_en="Xiranite",
            trade_value=1, production_rate=30.0,
            power_consumption=77.5,
            production_limit=60.0,  # Max 2 Forge of the Sky
        ),

        # Jincao Drink (錦草ソーダ)
        Product(
            id="jincao_drink", name_ja="錦草ソーダ", name_en="Jincao Drink",
            trade_value=16, production_rate=6.0,
            ferrium_ore=120.0, power_consumption=175.0,
        ),

        # Yazhen Syringe C (芽針注射剤I)
        Product(
            id="yazhen_syringe_c", name_ja="芽針注射剤I", name_en="Yazhen Syringe C",
            trade_value=16, production_rate=6.0,
            ferrium_ore=120.0, power_consumption=175.0,
        ),

        # LC Wuling Battery
        # Note: power_consumption (227.5) already includes xiranite production power
        # The xiranite_consumption is for the constraint that limits total xiranite usage
        Product(
            id="lc_wuling_battery", name_ja="小容量武陵バッテリー", name_en="LC Wuling Battery",
            trade_value=25, production_rate=6.0,
            originium_ore=180.0, power_consumption=227.5,
            xiranite_consumption=30.0,  # 5 xiranite per battery at 6/min (for constraint only)
            sandleaf_consumption=30.0,  # for dense originium powder
            is_battery=True, battery_power=1066.67,  # 1600 power * 40 sec / 60 sec/min
        ),
    ]

    return products


# =============================================================================
# LP Formulation
# =============================================================================

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


def solve_portfolio(region: RegionData, min_interval_hours: float) -> LPResult:
    """
    Solve the production portfolio optimization problem using LP.

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

    Decision variables:
        - production_rate for each non-battery product (or sale_rate for intermediates like xiranite)
        - production_rate for each battery product
        - power_rate for each battery (how much goes to power)
    """

    products = region.products
    n_products = len(products)

    # Identify batteries and intermediates (xiranite)
    battery_indices = [i for i, p in enumerate(products) if p.is_battery]
    xiranite_idx = next((i for i, p in enumerate(products) if p.id == "xiranite"), None)
    n_batteries = len(battery_indices)

    # Check if any product consumes xiranite
    has_xiranite_consumers = any(p.xiranite_consumption > 0 for p in products)

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
    ore_types = ["originium_ore", "amethyst_ore", "ferrium_ore"]
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

    # 5. Storage limit constraints
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
    bounds = []
    for i, p in enumerate(products):
        if p.id == "xiranite" and has_xiranite_consumers:
            # For xiranite with consumers, production_limit is handled above
            bounds.append((0, None))
        elif p.is_battery:
            # Battery bounds: production can be higher than sale (some goes to power)
            upper = p.production_limit if p.production_limit is not None else None
            bounds.append((0, upper))
        else:
            # Non-battery: sale rate = production rate, limited by storage
            upper_storage = max_sale_rate
            upper_limit = p.production_limit if p.production_limit is not None else None
            if upper_limit is not None:
                upper = min(upper_storage, upper_limit)
            else:
                upper = upper_storage
            bounds.append((0, upper))
    # Power rates for batteries
    for _ in range(n_batteries):
        bounds.append((0, None))

    # Convert to arrays
    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)

    # Solve
    result: OptimizeResult = linprog(
        c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs"
    )

    if not result.success:
        return LPResult(
            success=False,
            message=result.message,
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
    x = result.x
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
    lines.append("| Product | Rate (/min) | Originium | Amethyst | Ferrium | Power (unit/sec) | Price |")
    lines.append("|---------|------------|-----------|----------|---------|------------------|-------|")

    products_by_id = {p.id: p for p in region.products}

    total_orig = 0.0
    total_ameth = 0.0
    total_ferr = 0.0
    total_power = 0.0

    for prod_id, rate in sorted(result.production_rates.items()):
        p = products_by_id[prod_id]
        scale = rate / p.production_rate

        orig = p.originium_ore * scale
        ameth = p.amethyst_ore * scale
        ferr = p.ferrium_ore * scale
        power = p.power_consumption * scale

        total_orig += orig
        total_ameth += ameth
        total_ferr += ferr
        total_power += power

        orig_str = f"{orig:.0f}" if orig > 0 else "-"
        ameth_str = f"{ameth:.0f}" if ameth > 0 else "-"
        ferr_str = f"{ferr:.0f}" if ferr > 0 else "-"

        lines.append(f"| {p.name_en} | {rate:.2f} | {orig_str} | {ameth_str} | {ferr_str} | {power:.0f} | {p.trade_value} |")

    # Totals row
    orig_surplus = region.mining_rates.get("originium_ore", 0) - total_orig
    ameth_surplus = region.mining_rates.get("amethyst_ore", 0) - total_ameth
    ferr_surplus = region.mining_rates.get("ferrium_ore", 0) - total_ferr

    lines.append(f"| **Total** | | **{total_orig:.0f}** (surplus {orig_surplus:.0f}) | **{total_ameth:.0f}** (surplus {ameth_surplus:.0f}) | **{total_ferr:.0f}** (surplus {ferr_surplus:.0f}) | **{total_power:.0f}** | |")
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
    for prod_id, analysis in result.storage_analysis.items():
        p = products_by_id[prod_id]
        loss_value = analysis["storage_loss"] * p.trade_value
        total_loss_value += loss_value

        loss_str = f"{analysis['storage_loss']:.0f}" if analysis["storage_loss"] > 0 else "-"
        loss_pct_str = f"{analysis['loss_percent']:.1f}%" if analysis["loss_percent"] > 0 else "-"

        lines.append(f"| {p.name_en} | {analysis['production']:.0f} | {region.storage_limit} | {loss_str} | {loss_pct_str} |")

    if total_loss_value > 0:
        lines.append(f"| **Total Loss Value** | | | **{total_loss_value:.0f} tickets** | |")

    lines.append("")

    # Effective rate after storage loss
    interval_minutes = interval_hours * 60
    produced_tickets = result.ticket_rate * interval_minutes
    effective_tickets = produced_tickets - total_loss_value
    effective_rate = effective_tickets / interval_minutes

    lines.append("## Effective Rate")
    lines.append("")
    lines.append(f"| Interval | Production | Storage Loss | Effective | Effective Rate |")
    lines.append(f"|----------|------------|--------------|-----------|----------------|")
    lines.append(f"| {interval_hours}h | {produced_tickets:.0f} | {total_loss_value:.0f} | {effective_tickets:.0f} | **{effective_rate:.2f}/min** |")
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

    result = solve_portfolio(region, args.interval)

    if args.json:
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
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_output(region, result, args.interval))


if __name__ == "__main__":
    main()
