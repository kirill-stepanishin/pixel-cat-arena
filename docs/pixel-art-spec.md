# Pixel art production spec

This is the first asset sheet for the eight equipment archetypes, Mochi, and
the enemy cat. Rarity is a UI treatment, not a separate sprite set: one
equipment sprite supports common, rare, epic, and legendary variants.

## Shared technical rules

- Source canvas: **64 x 64 pixels** for every cat and equipment layer.
- Export: transparent PNG, RGBA, no background, no white matte.
- Display: nearest-neighbor scaling only; start at 4x (256 x 256).
- Pixel grid: draw on whole pixels; no anti-aliasing, blur, or sub-pixel paths.
- Outline: 1 px near-black outline (`#2b2340`) with selective 2 px corners on
  large silhouettes.
- Palette: maximum 16 colors per individual sprite, excluding transparency.
- Baseline: y=56. The cat's feet and all worn layers use this same baseline.
- Origin: x=0, y=0 at the top-left of the 64 x 64 canvas.
- Facing direction: player cat faces right; enemy cat uses the same source art
  mirrored horizontally in the renderer.
- Every layer must keep the full 64 x 64 canvas even when most pixels are
  transparent. Never crop an equipment layer.

## Base cat: Mochi

File: `frontend/public/assets/cats/mochi.png`

- Source art: grayscale, rear/three-quarter pose, tail extending toward the
  left. The source is already 64×64 RGBA and is used without resampling.
- Measured opaque bounds: x=3..60, y=2..60.
- Feet contact: approximately y=60.
- Head/ear zone: approximately x=20..48, y=2..27.
- Neck zone: approximately x=24..44, y=24..34.
- Torso overlay zone: approximately x=20..48, y=28..50.
- Forward paw/weapon zone: approximately x=42..58, y=30..48.
- Keep the tail unobstructed; body equipment should not assume a front-facing
  silhouette.
- Because this pose is rear-facing, headwear, bodywear, collar, and back-mounted
  accessories are the safest first overlays. Handheld weapons need a separate
  pose-specific anchor and should not be mirrored automatically.

## Enemy cat

File: `frontend/public/assets/cats/enemy-cat.png`

- Source art: red-eyed, front/three-quarter evil kitten with a reddish-brown
  palette. It is 64×64 RGBA and should be treated as a distinct enemy pose.
- Measured opaque bounds: x=11..58, y=3..59.
- Head/ear zone: approximately x=16..49, y=3..28.
- Chest/torso zone: approximately x=20..50, y=27..52.
- Keep the red eyes and face visible; enemy equipment is not required for the
  first pass.
- The enemy never receives equipment overlays. Render this as a standalone
  sprite in the opponent preview and battle scene.

## Equipment layers

All files live under `frontend/public/assets/items/` and use a transparent
64 x 64 canvas. The listed bounds are the maximum painted area, not a crop.
The eight player overlays are fitted to the downloaded Mochi pose. They are
player-only assets; the enemy sprite is always rendered without gear.

### Mochi overlay regions

These are the current pixel regions used by the fitted layers:

| Region | Pixel area | Notes |
|---|---|---|
| Head / ears | x=31..53, y=1..25 | Bunny Ears and Iron Helmet; keep face center x=40..45 clear |
| Collar / neck | x=29..47, y=28..42 | Follows the visible neck into upper chest |
| Body armor / jacket | x=21..48, y=27..51 | Stops above feet and leaves tail unobstructed |
| Forward claws | x=47..63, y=28..40 | Follows Mochi's raised forward paw |
| Wand | x=49..61, y=16..36 | Shares the forward paw grip and points up/right |
| Shield | x=46..58, y=31..47 | Held in front of the torso, away from the face |

All eight layers are rendered on the same 64×64 canvas. Non-weapon art is
currently cleared while the item system remains intact for future art passes.
The active weapon layers are fitted to Mochi's raised forward paw.

| File | Slot | Anchor and painted bounds | Art direction | Primary stat by rarity |
|---|---|---|---|---|
| `head/bunny-ears.png` | Head | x=14..50, y=5..28; ear roots at (21,23) and (43,23) | Two tall soft ears, one slightly bent; keep eyes and muzzle clear | SPD: 10–20 / 16–28 / 24–40 / 34–55 |
| `head/iron-helmet.png` | Head | x=12..52, y=9..29; lower rim y=28 | Rounded metal helmet with two ear cutouts and a bright highlight | DEF: 10–20 / 16–28 / 24–40 / 34–55 |
| `body/leather-armor.png` | Body | x=16..48, y=28..52; collar y=31 | Brown vest with two shoulder plates; leave paws and tail visible | DEF: 10–20 / 16–28 / 24–40 / 34–55 |
| `body/runner-jacket.png` | Body | x=15..49, y=27..52; collar y=30 | Bright short jacket with diagonal stripe; leave lower legs clear | SPD: 10–20 / 16–28 / 24–40 / 34–55 |
| `weapon/claw-gloves.png` | Weapon | x=43..61, y=32..49; grip/paw at (48,40) | Three small metallic claws projecting from the forward paw | ATK: 10–20 / 16–28 / 24–40 / 34–55 |
| `weapon/magic-wand.png` | Weapon | x=45..61, y=22..47; grip at (48,41) | Thin wand angled up-right with a one-pixel sparkle tip | SPD: 10–20 / 16–28 / 24–40 / 34–55 |
| `accessory/bell-collar.png` | Accessory | x=20..45, y=36..45; bell center (36,44) | Collar follows neck curve; gold bell hangs below chin | SPD: 10–20 / 16–28 / 24–40 / 34–55 |
| `accessory/tiny-shield.png` | Accessory | x=43..58, y=34..49; strap near (47,40) | Small shield held in front of the torso, not over the face | DEF: 10–20 / 16–28 / 24–40 / 34–55 |

The four values in each stat cell are **common / rare / epic / legendary**.
Each rare item also rolls one bonus stat from 4–8; epic rolls two bonuses
from 6–12; legendary rolls three bonuses from 8–16. Bonus stats can be ATK,
DEF, or SPD and may stack with the primary stat.

## Layer and overlap contract

Render in this exact order:

```text
base cat
body layer
accessory layer
head layer
weapon layer
```

Equipment pixels may overlap the cat, but must not erase the base layer. The
weapon is last so claws, wand, or shield remain readable over body equipment.
Head items must not paint below y=30 except for deliberate straps. Body items
must not paint above y=27 except for collars or shoulder straps.

## Animation-safe variants

For the first animation pass, create no separate animation sheets. The renderer
should translate, bounce, flash, and mirror these static layers as a composed
cat. If animated sprites are added later, keep the same 64 x 64 canvas, baseline,
anchor points, and layer order for every frame.

## Acceptance checklist

An asset is ready when it:

1. Opens as a 64 x 64 transparent PNG.
2. Shares the Mochi baseline and anchor points.
3. Reads clearly at 256 x 256 without smoothing.
4. Does not cover the eyes, muzzle, or feet unintentionally.
5. Looks correct when mirrored for the enemy side.
6. Works unchanged for every rarity; rarity color and border belong to the UI.
