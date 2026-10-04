# Pixel Cat Arena

Pixel Cat Arena is a browser-based multiplayer game about building the best
pixel-art cat. Players collect gear, customize their cat, fight quick
automatic battles, and trade equipment with other players.

The game is designed for a simple, satisfying loop:

```text
fight → earn currency and gear → improve your cat → trade → fight stronger opponents
```

It targets the **Game**, **Python**, and **Solana** hackathon tracks. The first
playable version is deliberately off-chain so the game can be made fun and
reliable quickly. Solana ownership and wallet features are added only after the
local game loop is complete.

## What the player does

### Build a unique cat

Every development player starts with one cat named Mochi, base stats
`Attack 12`, `Defense 10`, and `Speed 8`, plus 125 coins and four starter
items. The MVP frontend is a single-page dashboard:
the cat is the primary focus, with equipment, inventory, marketplace access,
and the current enemy/NPC visible without navigating between separate screens.
The first visual implementation uses CSS/Canvas placeholders; real transparent
pixel-art layers can replace them later without changing item ownership.

Players can equip one item in each slot:

- **Head** — helmets, hats, crowns, and other visual modifiers
- **Body** — armor, robes, jackets, and defensive gear
- **Weapon** — swords, wands, claws, and offensive gear
- **Accessory** — capes, charms, shields, and stat-boosting extras

Items have a rarity and three simple stats: **Attack**, **Defense**, and
**Speed**. Common gear is accessible and reliable; rare gear is more powerful
and desirable in the marketplace.

### Fight automatic battles

Battles are short PvE encounters against enemies with different stats and
difficulty levels. The backend calculates and persists the result, while the
browser displays the completed outcome:

1. The server snapshots the cat's equipment and stats.
2. A deterministic battle seed controls turn order and random events.
3. The fighters attack automatically until one wins.
4. The server stores the result, awards stage-scaled rewards on wins, and
   advances the highest unlocked opponent.
5. The dashboard plays the persisted event log, then displays the authoritative
   result, reward, and next opponent.

The PvE roster is infinite and scales linearly. The latest unlocked stage is
the default opponent, while an arena selector allows replaying any defeated
stage. Replays grant that stage's normal coins and loot table without
advancing progression. Rewards are persisted atomically with the battle and
duplicate item drops are valid.

This keeps combat fair, deterministic, and easy to extend to asynchronous PvP.

### Earn, equip, and trade

Victories provide in-game currency and a chance to find new gear. Players can
compare item stats in their inventory, equip upgrades, and list unwanted gear
on the marketplace. Other players can browse listings and buy items using
in-game currency.

Marketplace purchases are handled as atomic PostgreSQL transactions, preventing
double purchases, duplicated items, and negative balances.

### Challenge saved builds

After PvE and the marketplace are working, players can publish a saved build.
Other players can challenge that build while its owner is offline. Both sides
use the same deterministic combat service, so asynchronous PvP adds
competition without requiring real-time networking.

## What the app looks like

Pixel Cat Arena should feel like a compact one-page pixel-art game dashboard
rather than a large administration app:

```text
┌─────────────────────────────────────────────────────────────────────┐
│ PIXEL CAT ARENA              125 coins       Marketplace            │
├───────────────────────────────┬─────────────────────────────────────┤
│          [pixel cat]           │  EQUIPMENT / INVENTORY              │
│       ATK 16 (+4)              │  Head: Woven Cap       +1 SPD       │
│       DEF 12 (+2)              │  Body: Copper Vest     +2 DEF       │
│       SPD 10 (+2)              │  Weapon: Pixel Sword   +3 ATK       │
│                               │  Accessory: Lucky Charm +2         │
│       [FIGHT A BATTLE]         │  [MARKETPLACE]  [ENEMY / NPC]       │
└───────────────────────────────┴─────────────────────────────────────┘
```

The one-page dashboard contains:

- **Cat panel:** placeholder cat visual, computed stats, and future fight action
- **Equipment/inventory panel:** four slots, item cards, rarity, modifiers, and
  equip/unequip actions
- **Marketplace panel:** access point for future browsing and trading
- **Enemy/NPC panel:** placeholder opponent area that can later support PvE and
  saved-build PvP

The visual style should use crisp nearest-neighbor pixel art, a limited bright
color palette, chunky borders, readable stat badges, and lightweight
animations. Gear is composited in a fixed order:

```text
base cat → body → accessory → head → weapon
```

## Technology

- **Frontend:** TypeScript, Vite, HTML/CSS, and Canvas 2D
- **Backend:** Python 3.12 and FastAPI
- **Database:** Tiger Data / Tiger Cloud PostgreSQL
- **Persistence:** SQLAlchemy 2 and Alembic migrations
- **Testing:** Pytest for API and game rules; Vitest for frontend utilities
- **Blockchain:** Solana wallet and asset support in a later phase

Tiger Data provides a managed PostgreSQL foundation with standard SQL, which
keeps the hackathon setup small while leaving room for fast battle history,
marketplace queries, and time-series gameplay analytics.

## MVP target

The current playable slice lets a player create a development identity, receive
a starter cat and gear, equip items, and fight an infinite deterministic PvE
roster. Battles, snapshots, events, equipment, enemy progression, scaled
rewards, and battle/reward history are persisted and server-authoritative. The
dashboard includes enemy selection, timed battle playout, skip-to-result, and
post-playback reward notifications. Marketplace and asynchronous PvP remain
future work.

The eventual MVP will let a player earn persistent rewards and buy or sell
items. Combat, inventory ownership, rewards, and marketplace transfers will
remain server-authoritative and stored in Tiger Data.

The detailed sequential build plan, schema, API slices, technical decisions,
and current implementation status live in [`AGENTS.md`](AGENTS.md).

## Project status

The repository contains a tested backend and frontend through deterministic PvE:
player/cat persistence, starter inventory, authoritative equipment actions,
computed stat overlays, a persisted Dummy 1–3 opponent roster, deterministic
battle seeds and snapshots, ordered battle events, and a direct Fight flow.
The frontend calls `POST /dev/player` on startup and retains the returned
player ID in browser storage. Rewards and progression beyond opponent
advancement are not implemented yet; reward/economy decisions and the
corresponding dashboard updates are the next planning step. The detailed
implementation state is tracked in [`AGENTS.md`](AGENTS.md).
