# Item balance matrix

Items roll one slot-themed primary stat. Rarity adds independent bonus stat
rolls; bonus stats may be any of Attack, Defense, or Speed. A bonus roll on the
same stat stacks with the primary roll.

| Rarity | Primary pool | Bonus sets | Bonus pool | Approx. total power |
|---|---:|---:|---:|---:|
| Common | 10–20 | 0 | — | 10–20 |
| Rare | 16–28 | 1 | 4–8 | 20–36 |
| Epic | 24–40 | 2 | 6–12 | 36–64 |
| Legendary | 34–55 | 3 | 8–16 | 58–103 |

`Approx. total power` is the min/max sum of all rolls. It is a tuning guide,
not a combat rating. The first content pass includes two item archetypes per
slot; each archetype is available in every rarity. This gives the game eight
visual items and 32 balanceable definitions without requiring 32 separate
sprites.

| Slot | Archetype | Primary stat |
|---|---|---|
| Head | Bunny Ears | Speed |
| Head | Iron Helmet | Defense |
| Body | Leather Armor | Defense |
| Body | Runner Jacket | Speed |
| Weapon | Claw Gloves | Attack |
| Weapon | Magic Wand | Speed |
| Accessory | Bell Collar | Speed |
| Accessory | Tiny Shield | Defense |

The starter items use common variants and retain small fixed values so the
opening cat remains close to the documented `12/10/8` base build. Newly dropped
instances use the rarity pools above. Early stages introduce common gear first,
then rare at stage 5, epic at stage 10, and legendary at stage 20. The reward
service rolls with the persisted battle seed, so the same battle remains
deterministic.

## Tuning assumptions

- Common gear is a predictable progression item and should not invalidate the
  starter loadout immediately.
- Rare gear is a meaningful upgrade, with one flexible bonus that creates build
  variation.
- Epic gear is exciting but uncommon; two bonuses make it visibly distinct.
- Legendary gear is reserved for stage 20+ drops.
- No negative modifiers are rolled in this system.
- The four slots have equal presentation weight, while their primary stat
  identity keeps builds legible.
