# Pixel Cat Arena Engineering Plan

This file is the implementation guide for Pixel Cat Arena. `README.md` is the
product-facing overview; this file records the current state, boundaries, and
next work.

## Current implementation state

**Status:** The local single-player PvE foundation is complete. The next goal
is a local two-player demo using two browser sessions and one backend process.
Accounts, instant selling, marketplace trading, and asynchronous PvP are not
implemented yet. Hosting is explicitly out of scope for this milestone.

- [x] Product concept and MVP loop documented
- [x] Backend and frontend scaffolds
- [x] Configurable database connection and health check
- [x] Player, cat, and currency persistence
- [x] Item definitions and item instances
- [x] Equipment ownership validation and four equipment slots
- [x] Single-page inventory/equipment dashboard
- [x] Layered cat equipment visuals
- [x] Deterministic server-authoritative PvE
- [x] Persistent battle events, rewards, and enemy progression
- [ ] Accounts and authenticated sessions
- [ ] Instant item selling
- [ ] Fixed-price marketplace
- [ ] Asynchronous PvP
- [ ] Local two-player smoke test
- [ ] Visual polish and analytics
- [ ] Solana NFT integration

### What works now

The development player is provisioned as `dev-player`, with one cat named
Mochi, base stats `12/10/8` for attack/defense/speed, 125 starter coins, and
four starter items. The browser calls `POST /dev/player`, loads the inventory,
and refreshes authoritative state after equipment actions.

The backend persists item definitions and rolled item modifiers separately.
Equipment is limited to one item per slot. Cat layers always render in this
order, regardless of API or equip order:

```text
base cat → body → accessory → head → weapon
```

PvE uses snapshots and a persisted seed. Turns are speed-based and deterministic
for a given snapshot and seed. Combat has no draw result: it runs until a
fighter reaches zero HP, and every attack deals at least one damage after
defense reduction. Victories grant stage-scaled coins and may grant a
deterministically selected item drop. Duplicate item instances are valid.

The frontend shows the cat, computed totals, equipment names, rarity, stat
modifiers, inventory items, enemy selection, battle playback, rewards, loading
states, errors, and pending actions. Equipment pictures are shown on the cat;
the inventory and equipment sidebar use text, rarity color, and stat values.

## Technical stack

- Python 3.12
- FastAPI and Pydantic
- TypeScript and Vite
- SQLAlchemy 2 and Alembic
- SQLite for local development
- PostgreSQL-compatible SQLAlchemy support can be added later if public hosting
  becomes necessary
- Pytest and Vitest

The database is selected through `DATABASE_URL`. Do not assume a provider in
application code or documentation. The local default is SQLite:

```text
DATABASE_URL=sqlite+aiosqlite:///./pixel_cat_arena.db
```

The backend intentionally reports `503` from `/health` when the database is
missing or unavailable. This makes configuration failures explicit rather than
presenting a false healthy state.

## Scaffold commands

```text
cp .env.example .env
make install
make backend
make frontend
make test
```

## Product and engineering boundaries

- Keep stats in one validated stat/modifier model.
- Keep cats, enemies, and items data-driven.
- Keep route handlers and UI screens thin; put rules in backend services.
- Keep combat, ownership, rewards, sale prices, and marketplace transfers
  server-authoritative.
- Keep equipment composition player-only; enemy sprites are standalone.
- Do not add Solana as a runtime requirement.
- Do not build live networking; asynchronous saved-build PvP is sufficient.
- Do not add timed bidding before fixed-price trading is reliable.

## Sequential implementation plan

### Phase 0 — Foundation

Complete. Backend/frontend manifests, environment loading, database access,
Alembic migrations, health endpoint, Vite shell, and local commands exist.

### Phase 1 — Player and cat

Complete. Player, cat, currency, starter data, schemas, services, routes, and
the validated stat model exist. Identity is still the temporary development
player and is not authentication.

### Phase 2 — Items and equipment

Complete. Item definitions/instances, four slots, starter gear, rolled
modifiers, ownership checks, equipment actions, stat overlays, layered
placeholder visuals, and the single-page dashboard exist.

### Phase 3 — Deterministic PvE

Complete. Infinite linearly scaled Dummy enemies, current-enemy persistence,
combat snapshots, seeds, ordered events, speed-based turns, minimum damage of
one, victory/defeat outcomes, and the Fight flow exist.

### Phase 4 — Rewards and progression

Complete. Stage-scaled coins, deterministic item drops, duplicate instances,
battle-keyed reward persistence, enemy progression, defeated-enemy selection,
battle/reward history, timed playback, and skip-to-result exist.

### Phase 5 — Local accounts and sessions

1. Add a password hash to players through a migration.
2. Add register, login, current-user, and logout/session behavior.
3. Use authenticated identity for protected player, item, battle, and currency
   operations instead of trusting arbitrary player IDs from the browser.
4. Keep scope small: no email verification, password reset, OAuth, or wallet
   login.

**Exit criteria:** Two players can register, log in, log out, and reload their
own independent cats, inventories, currency, and PvE progress from separate
browser tabs or profiles while sharing the same local backend and SQLite file.

### Phase 6 — Instant selling

1. Add a server-side sale endpoint.
2. Calculate value from rarity and rolled stats.
3. Prevent selling equipped or listed items.
4. Credit currency and remove the item in one transaction.
5. Add frontend confirmation, price display, and refreshed inventory/balance.

**Exit criteria:** A player can sell an eligible item exactly once and receive
the server-calculated value.

### Phase 7 — Local fixed-price marketplace

1. Add listing, seller, item, price, status, buyer, and timestamps.
2. Add listing creation, active-listing browsing, cancellation, and purchase.
3. Lock listing, item, and currency rows during purchase.
4. Prevent self-purchases, double purchases, negative balances, and transfers
   of equipped or already listed items.
5. Add filtering by slot and rarity.

**Exit criteria:** Two local accounts can list, browse, purchase, cancel, and
reconcile item ownership and currency without duplication or double spending.

### Phase 8 — Local asynchronous PvP

1. Add immutable published build snapshots.
2. Publish the current cat, equipment, and computed stats.
3. Challenge another player by username or player ID.
4. Reuse deterministic combat against the saved opponent snapshot.
5. Persist both participant snapshots, seed, events, result, and timestamps.
6. Add challenge/result history.

**Exit criteria:** One local account can challenge another account's saved
build from a separate tab, resolve the match server-side, and later view the
authoritative result without mutating the opponent's current inventory.

### Phase 9 — Local demo verification and targeted polish

1. Run one backend process, one frontend dev server, and the local SQLite
   database.
2. Open two tabs or browser profiles and register separate accounts.
3. Test PvE, item sale, listing, purchase, cancellation, and asynchronous PvP
   from both accounts.
4. Add only high-value polish: readable loading/error/pending states, clear
   account identity, inventory sorting/filtering, and battle feedback.
5. Keep a repeatable local demo script and reset procedure.

### Phase 10 — Future hosting and Solana

Deferred. Public hosting, PostgreSQL migration, wallet connection, verified
wallet association, and legendary NFT ownership are future work. None is
required for the local demo. If hosting is later requested, first migrate the
database and test marketplace concurrency before exposing the app publicly.

## Data model

| Table | Purpose |
|---|---|
| `players` | Account identity, display name, and future password hash |
| `cats` | Player cat and base stats |
| `currencies` | Player balance |
| `item_definitions` | Static item type, slot, rarity, visual, and roll rules |
| `item_instances` | Owned item, rolled modifiers, and equipment state |
| `enemies` | PvE enemy definitions |
| `battles` | Participants, seed, snapshots, result, and timestamps |
| `battle_events` | Ordered persisted combat events |
| `rewards` | Battle rewards and item drops |
| `marketplace_listings` | Fixed-price item listings and transfer state |
| `build_snapshots` | Immutable saved builds for asynchronous PvP |

Use foreign keys, unique constraints for equipment slots, non-negative
currency constraints where practical, and transactions for rewards, sales,
and marketplace operations.

## API sequence

Current endpoints:

```text
GET  /health
POST /dev/player
GET  /players/{player_id}
GET  /players/{player_id}/items
GET  /players/items/definitions
POST /players/{player_id}/cats/{cat_id}/items/{item_id}/equip
POST /players/{player_id}/cats/{cat_id}/items/{item_id}/unequip
POST /battles/pve
GET  /battles/{battle_id}
GET  /battles/pve/current/{player_id}
GET  /battles/pve/enemies/{player_id}
GET  /battles/players/{player_id}/history
GET  /battles/players/{player_id}/rewards
```

Next endpoints:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
POST /players/items/{item_id}/sell
POST /marketplace/listings
GET  /marketplace/listings
POST /marketplace/listings/{listing_id}/buy
POST /marketplace/listings/{listing_id}/cancel
POST /pvp/builds/publish
POST /pvp/challenges
GET  /pvp/challenges
GET  /pvp/challenges/{challenge_id}
```

## Engineering rules

- Build and verify one phase before starting the next.
- Prefer precise validation and explicit API errors.
- Never silently fall back on invalid ownership, balance, or battle state.
- Keep the client from choosing winners, rewards, prices, or transfer results.
- Keep SQLAlchemy and Alembic boundaries clean so a future PostgreSQL migration
  does not require a domain rewrite.
- Update this file's checklist whenever a phase meaningfully changes.
