from itertools import pairwise

from app.content.items import ITEM_ARCHETYPES, ITEM_TEMPLATES, RARITY_RULES, roll_modifiers


def test_catalog_has_two_archetypes_and_all_rarity_variants_per_slot() -> None:
    slots = {template["slot"] for template in ITEM_TEMPLATES}
    assert slots == {"head", "body", "weapon", "accessory"}
    assert len(ITEM_ARCHETYPES) == 8
    assert all(sum(archetype[2] == slot for archetype in ITEM_ARCHETYPES) == 2 for slot in slots)
    assert len(ITEM_TEMPLATES) == 32
    assert all(
        {template["rarity"] for template in ITEM_TEMPLATES if template["slot"] == slot}
        == set(RARITY_RULES)
        for slot in slots
    )
    assert all(
        sum(template["id"].rsplit("-", 1)[0] == archetype[0] for template in ITEM_TEMPLATES) == 4
        for archetype in ITEM_ARCHETYPES
    )


def test_rarity_rules_add_bonus_sets_and_grow_primary_pool() -> None:
    rarities = ("common", "rare", "epic", "legendary")
    for previous, current in pairwise(rarities):
        assert RARITY_RULES[current]["primary_max"] > RARITY_RULES[previous]["primary_max"]
        assert RARITY_RULES[current]["bonus_stat_count"] == RARITY_RULES[previous]["bonus_stat_count"] + 1


def test_item_roll_is_deterministic_and_has_expected_shape() -> None:
    template = next(template for template in ITEM_TEMPLATES if template["rarity"] == "rare")
    first = roll_modifiers(template, seed=42)
    second = roll_modifiers(template, seed=42)

    assert first == second
    assert template["primary_stat"] in first
    assert sum(first.values()) >= template["primary_min"] + template["bonus_min"]
