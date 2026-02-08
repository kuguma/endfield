#!/usr/bin/env python3
"""Verify power consumption calculations for Valley IV products.

Traces through production chains to calculate total power consumption
including mining, farming, and processing.
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Machine:
    name: str
    power: int


MACHINES = {
    "shredding_unit": Machine("Shredding Unit", 5),
    "refining_unit": Machine("Refining Unit", 5),
    "moulding_unit": Machine("Moulding Unit", 10),
    "fitting_unit": Machine("Fitting Unit", 20),
    "grinding_unit": Machine("Grinding Unit", 50),
    "filling_unit": Machine("Filling Unit", 20),
    "packaging_unit": Machine("Packaging Unit", 20),
}

# Mining power per ore/min
# Electric Mining Rig: 5 power, 20/min
# Electric Mining Rig Mk II: 10 power, 20/min
MINING_POWER_PER_UNIT = {
    "originium_ore": 5 / 20,  # 0.25 unit/sec per ore/min
    "amethyst_ore": 5 / 20,   # 0.25
    "ferrium_ore": 10 / 20,   # 0.5
}

# Farming power per plant/min
# Planting: 20 power, 30/min
# Seed-Picking: 10 power, 60/min (so 30 power total for sustainable loop)
FARMING_POWER_PER_UNIT = 30 / 30  # 1.0 unit/sec per plant/min


def load_recipes():
    """Load recipes from JSON file."""
    path = Path(__file__).parent.parent / "recipes.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_production_chain(
    recipes: dict,
    target_item: str,
    target_rate_per_min: float,
    power_breakdown: dict = None,
) -> tuple[float, dict, dict]:
    """
    Calculate total power and resource consumption for producing an item.

    Returns:
        (total_power_per_sec, ore_consumption_per_min, plant_consumption_per_min)
    """
    if power_breakdown is None:
        power_breakdown = {}

    ore_consumption = {}
    plant_consumption = {}
    total_power = 0.0

    # Check if this is a raw material
    items = recipes.get("items", {})
    item_info = items.get(target_item, {})
    item_type = item_info.get("type", "")

    if item_type == "raw_ore":
        # Ore - add mining power
        mining_power = MINING_POWER_PER_UNIT.get(target_item, 0) * target_rate_per_min
        ore_consumption[target_item] = target_rate_per_min
        return mining_power, ore_consumption, plant_consumption

    if item_type == "raw_plant":
        # Plant - add farming power
        farming_power = FARMING_POWER_PER_UNIT * target_rate_per_min
        plant_consumption[target_item] = target_rate_per_min
        return farming_power, ore_consumption, plant_consumption

    # Find recipe for this item
    recipe_data = recipes.get("recipes", {})
    recipe = recipe_data.get(target_item)

    if not recipe:
        # No recipe found - might be raw material
        print(f"Warning: No recipe found for {target_item}")
        return 0.0, ore_consumption, plant_consumption

    machine_name = recipe["machine"]
    time_sec = recipe["time_sec"]
    inputs = recipe.get("inputs", {})
    outputs = recipe.get("outputs", {target_item: 1})
    output_count = outputs.get(target_item, 1)

    # Calculate machine throughput and count
    output_per_sec = output_count / time_sec
    output_per_min = output_per_sec * 60

    machines_needed = target_rate_per_min / output_per_min
    machine = MACHINES.get(machine_name)

    if machine:
        machine_power = machines_needed * machine.power
        total_power += machine_power

        # Track breakdown
        if machine_name not in power_breakdown:
            power_breakdown[machine_name] = 0
        power_breakdown[machine_name] += machine_power

    # Recursively process inputs
    for input_item, input_count in inputs.items():
        # How much of this input do we need per minute?
        input_per_output = input_count / output_count
        input_rate_per_min = input_per_output * target_rate_per_min

        sub_power, sub_ore, sub_plant = calculate_production_chain(
            recipes, input_item, input_rate_per_min, power_breakdown
        )

        total_power += sub_power

        for ore, amount in sub_ore.items():
            ore_consumption[ore] = ore_consumption.get(ore, 0) + amount

        for plant, amount in sub_plant.items():
            plant_consumption[plant] = plant_consumption.get(plant, 0) + amount

    return total_power, ore_consumption, plant_consumption


def main():
    recipes = load_recipes()

    products = [
        ("origocrust", 30),
        ("amethyst_bottle", 30),
        ("amethyst_part", 30),
        ("ferrium_part", 30),
        ("steel_part", 30),
        ("buck_capsule_c", 6),
        ("buck_capsule_b", 6),
        ("buck_capsule_a", 6),
        ("canned_citrome_c", 6),
        ("canned_citrome_b", 6),
        ("canned_citrome_a", 6),
        ("lc_valley_battery", 6),
        ("sc_valley_battery", 6),
        ("hc_valley_battery", 6),
    ]

    print("=" * 100)
    print(f"{'Product':<25} {'Rate':<8} {'Power':>10} {'Orig Ore':>10} {'Ame Ore':>10} {'Fer Ore':>10} {'Plants':>10}")
    print("=" * 100)

    for product_id, rate in products:
        power_breakdown = {}
        power, ore, plant = calculate_production_chain(recipes, product_id, rate, power_breakdown)

        orig = ore.get("originium_ore", 0)
        ame = ore.get("amethyst_ore", 0)
        fer = ore.get("ferrium_ore", 0)
        plant_total = sum(plant.values())

        items = recipes.get("items", {})
        item_info = items.get(product_id, {})
        name = item_info.get("name_ja", product_id)

        print(f"{name:<25} {rate:<8} {power:>10.1f} {orig:>10.0f} {ame:>10.0f} {fer:>10.0f} {plant_total:>10.0f}")

    print("=" * 100)
    print("\nDetailed breakdown for key products:\n")

    # Detailed breakdown for カプセルⅢ
    print("蕎花カプセルⅢ @ 6/min:")
    power_breakdown = {}
    power, ore, plant = calculate_production_chain(recipes, "buck_capsule_a", 6, power_breakdown)

    print(f"  Total power: {power:.1f} unit/sec")
    print(f"  Ore: originium={ore.get('originium_ore', 0):.0f}, amethyst={ore.get('amethyst_ore', 0):.0f}, ferrium={ore.get('ferrium_ore', 0):.0f}")
    print(f"  Plants: {plant}")
    print("  Power breakdown by machine:")
    for machine, pwr in sorted(power_breakdown.items(), key=lambda x: -x[1]):
        print(f"    {machine}: {pwr:.1f} unit/sec")

    # Calculate mining portion
    mining_power = (
        ore.get("originium_ore", 0) * MINING_POWER_PER_UNIT.get("originium_ore", 0) +
        ore.get("amethyst_ore", 0) * MINING_POWER_PER_UNIT.get("amethyst_ore", 0) +
        ore.get("ferrium_ore", 0) * MINING_POWER_PER_UNIT.get("ferrium_ore", 0)
    )
    farming_power = sum(plant.values()) * FARMING_POWER_PER_UNIT
    processing_power = power - mining_power - farming_power

    print(f"  Mining power: {mining_power:.1f} unit/sec")
    print(f"  Farming power: {farming_power:.1f} unit/sec")
    print(f"  Processing power: {processing_power:.1f} unit/sec")

    # Compare with documented values
    print("\n" + "=" * 100)
    print("Comparison with documented values:\n")
    print(f"{'Product':<25} {'Calculated':>12} {'opt_sample':>12} {'opt_solved':>12} {'Diff (calc-sample)':>18}")
    print("-" * 100)

    comparisons = [
        ("buck_capsule_a", 6, 412, 92),
        ("canned_citrome_a", 6, 412, 92),
        ("lc_valley_battery", 6, 78, 55),
        ("sc_valley_battery", 6, 195, 85),
        ("hc_valley_battery", 6, 515, 398),
    ]

    for product_id, rate, opt_sample, opt_solved in comparisons:
        power_breakdown = {}
        power, _, _ = calculate_production_chain(recipes, product_id, rate, power_breakdown)

        items = recipes.get("items", {})
        item_info = items.get(product_id, {})
        name = item_info.get("name_ja", product_id)

        diff = power - opt_sample
        print(f"{name:<25} {power:>12.1f} {opt_sample:>12} {opt_solved:>12} {diff:>+18.1f}")


if __name__ == "__main__":
    main()
