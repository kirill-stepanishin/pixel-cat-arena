from __future__ import annotations

import random
from typing import TypedDict

StatKey = str


class ItemTemplate(TypedDict):
    id: str
    name: str
    slot: str
    rarity: str
    visual_key: str
    primary_stat: StatKey
    primary_min: int
    primary_max: int
    bonus_stat_count: int
    bonus_min: int
    bonus_max: int


RARITY_RULES = {
    "common": {"primary_min": 10, "primary_max": 20, "bonus_stat_count": 0, "bonus_min": 0, "bonus_max": 0},
    "rare": {"primary_min": 16, "primary_max": 28, "bonus_stat_count": 1, "bonus_min": 4, "bonus_max": 8},
    "epic": {"primary_min": 24, "primary_max": 40, "bonus_stat_count": 2, "bonus_min": 6, "bonus_max": 12},
    "legendary": {"primary_min": 34, "primary_max": 55, "bonus_stat_count": 3, "bonus_min": 8, "bonus_max": 16},
}


def _item(
    archetype_id: str,
    name: str,
    slot: str,
    rarity: str,
    visual_key: str,
    primary_stat: StatKey,
) -> ItemTemplate:
    return {
        "id": f"{archetype_id}-{rarity}",
        "name": name,
        "slot": slot,
        "rarity": rarity,
        "visual_key": visual_key,
        "primary_stat": primary_stat,
        **RARITY_RULES[rarity],
    }


ITEM_ARCHETYPES = (
    ("bunny-ears", "Bunny Ears", "head", "bunny-ears", "speed"),
    ("iron-helmet", "Iron Helmet", "head", "iron-helmet", "defense"),
    ("leather-armor", "Leather Armor", "body", "leather-armor", "defense"),
    ("runner-jacket", "Runner Jacket", "body", "runner-jacket", "speed"),
    ("claw-gloves", "Claw Gloves", "weapon", "claw-gloves", "attack"),
    ("magic-wand", "Magic Wand", "weapon", "magic-wand", "speed"),
    ("bell-collar", "Bell Collar", "accessory", "bell-collar", "speed"),
    ("tiny-shield", "Tiny Shield", "accessory", "tiny-shield", "defense"),
)

ITEM_TEMPLATES: tuple[ItemTemplate, ...] = tuple(
    _item(archetype_id, name, slot, rarity, visual_key, primary_stat)
    for archetype_id, name, slot, visual_key, primary_stat in ITEM_ARCHETYPES
    for rarity in RARITY_RULES
)

STARTER_ITEM_IDS = (
    "bunny-ears-common",
    "leather-armor-common",
    "claw-gloves-common",
    "bell-collar-common",
)


def roll_modifiers(template: ItemTemplate, seed: int) -> dict[str, int]:
    """Roll one deterministic primary stat and rarity-defined bonus stats."""
    rng = random.Random(seed)
    modifiers = {template["primary_stat"]: rng.randint(template["primary_min"], template["primary_max"])}
    stats = ("attack", "defense", "speed")
    for _ in range(template["bonus_stat_count"]):
        stat = rng.choice(stats)
        modifiers[stat] = modifiers.get(stat, 0) + rng.randint(template["bonus_min"], template["bonus_max"])
    return modifiers
