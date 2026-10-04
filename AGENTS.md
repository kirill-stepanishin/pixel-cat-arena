# Pixel Cat Arena Engineering Plan

This file is the working guide for implementing Pixel Cat Arena. Keep it
updated as each milestone is completed. `README.md` is the product-facing
description; this file contains implementation detail and agent guidance.

## Current implementation state

**Status:** Phases 0–3 are complete. The next active slice is transactional
rewards and progression after a PvE win.

- [x] Product concept and MVP loop documented
- [x] Sequential implementation phases defined
- [x] Tiger Data selected as the production database foundation
- [x] Solana explicitly deferred until the local game is stable
- [x] Backend scaffold
- [x] Frontend scaffold
- [x] Tiger Data connection and health check
- [x] Player and cat persistence
- [x] Inventory and equipment
- [x] Deterministic PvE
- [ ] Rewards and progression
- [ ] Marketplace
- [ ] Asynchronous PvP
- [ ] Hackathon polish and analytics
- [ ] Solana wallet and asset integration

Completed implementation summary: the independent backend and frontend shells,
SQLite-compatible local development path, development-player provisioning,
player/cat persistence, starter inventory, authoritative equipment actions,
computed stat overlays, persisted deterministic battle seeds/snapshots/events,
per-player Dummy 1–3 progression, and the direct Fight dashboard flow.
The Fight action also resets its pending state after successful or failed
requests so the control remains usable.

Key decisions: SQLite is supported locally while Tiger Cloud remains optional;
MVP identity is the unauthenticated `dev-player`; the frontend stays
single-page; and the server remains authoritative for equipment, combat
results, and future rewards.

Current gameplay defaults are intentionally small: a development player named
`dev-player`, one cat named Mochi with base stats `12/10/8` for
attack/defense/speed, `125` starter coins, and four starter items covering the
four equipment slots. No authentication, battle result, or marketplace
behavior is assumed yet.

Before adding content, preserve these extension boundaries:

- Keep stats in one validated stat/modifier model; do not scatter fixed stat
  fields through routes, combat, and UI.
- Keep cats, enemies, and items data-driven; isolate exceptional behavior in
  abilities or strategies rather than type checks throughout the codebase.
- Keep route handlers and UI screens thin; put rules in backend services and
  presentation state in frontend modules.

### Scaffold commands

```text
cp .env.example .env
make install
make backend
make frontend
make test
```

The backend intentionally reports `503` from `/health` until
`DATABASE_URL` is configured and Tiger Data can answer `SELECT 1`. This makes
missing infrastructure explicit instead of presenting a false healthy state.

## Technical stack

### Runtime and application layers

- Python 3.12
- FastAPI and Pydantic
- TypeScript and Vite
- HTML/CSS and Canvas 2D
- SQLAlchemy 2
- Alembic
- PostgreSQL-compatible SQL

### Infrastructure

- Tiger Data / Tiger Cloud PostgreSQL
- `DATABASE_URL` supplied through environment configuration
- Docker support after the local development loop is working

### Testing

- Pytest for API, persistence, combat, rewards, and transaction behavior
- Vitest for sprite composition, client state, and display helpers
- API smoke checks for the health endpoint and the main player flow

### Later blockchain layer

- Solana wallet connection in the frontend
- Backend nonce/signature verification
- A local ownership implementation first
- A Solana ownership implementation for selected rare items later

Do not make Solana a runtime requirement for the MVP. Keep gameplay state,
normal currency, battles, rewards, and ordinary marketplace operations in Tiger
Data unless a later product decision explicitly moves them on-chain.

## Repository layout

Create this structure during Phase 0:

```text
backend/
  app/
    main.py
    config.py
    db.py
    models/
    schemas/
    api/
    services/
  migrations/
  tests/
frontend/
  src/
    api/
    state/
    screens/
    rendering/
    styles/
  public/assets/
  tests/
scripts/
docker-compose.yml
Makefile
```

Keep domain rules in backend services rather than route handlers. Keep the
frontend responsible for presentation, input, and animation, never for
authoritative rewards or combat outcomes.

## Sequential implementation plan

### Phase 0 — Foundation

Completed: backend/frontend manifests, environment loading, SQLAlchemy, Alembic,
the health endpoint, Vite shell, and local commands.

**Exit criteria:** Both services start and `/health` reports database status.

### Phase 1 — Player and cat

Completed: player/cat/currency persistence, starter data, schemas, services,
routes, and the validated stat model. The development player is `dev-player`
with Mochi, base stats `12/10/8`, and 125 coins.

**Exit criteria:** A development player persists with the same cat and balance.

### Phase 2 — Items and equipment

Completed: item definitions/instances, four slots, structured stat modifiers,
starter gear, ownership validation, one equipped item per slot, and the
single-page dashboard with inventory, equipment, stat overlays, placeholder
visuals, and loading/error/pending states.

### Frontend product assumptions

- The MVP uses one page rather than separate inventory, marketplace, profile,
  and arena routes.
- The development player starts as `dev-player` with Mochi, 125 coins, and the
  four seeded starter items; this is temporary identity/data, not an auth
  design.
- The page presents the player's cat as the primary focus, with inventory,
  equipment, marketplace access, and the current enemy/NPC in the same view.
- The first enemy area is the current PvE opponent. It becomes interactive
  through the direct Fight action; no replay system is needed.
- The frontend automatically provisions the unauthenticated development player
  through `POST /dev/player` and stores the returned ID in browser storage.
- Placeholder visuals are intentional for now; no art asset pipeline is
  required before the next phase.
- Stat displays show both totals and equipment contributions.
- Server responses, not local guesses, define ownership and equipment state.

### Phase 3 — Deterministic PvE

Completed: a data-driven Dummy 1–3 roster, fixed-HP combat snapshots,
speed-based deterministic resolution, persisted seeds and ordered battle
events, per-player current-enemy persistence, and
`POST /battles/pve` plus `GET /battles/{battle_id}`. The dashboard directly
starts fights, displays authoritative results, advances the roster after wins,
and keeps the Fight control usable after completion. No rewards are granted.

The player-facing progression slice is complete:

1. Seed three ordered enemies: `Dummy 1`, `Dummy 2`, and `Dummy 3`, with
   increasing stats and stable IDs that can be renamed later.
2. Persist each player's current PvE enemy, starting at `Dummy 1`.
3. Make the PvE endpoint fight the player's current enemy without accepting an
   arbitrary enemy ID from the client.
4. Advance to the next dummy only after a player win; retain the same dummy
   after a loss or draw. Keep `Dummy 3` current after it is defeated.
5. Add the dashboard Fight action. Show the server's completed result and
   current enemy state directly; do not add battle replay.
6. Keep rewards deferred. Wins advance progression only; losses and draws grant
   neither rewards nor progression.
7. Test roster seeding, per-player persistence, win advancement, loss/draw
   retention, maximum progression, and authoritative result handling.

**Exit criteria:** Refreshing preserves each player's current dummy, a win
advances exactly one level, a loss/draw leaves the enemy unchanged, and the
browser never computes the battle result or progression. Complete.

### Phase 4 — Rewards and progression

Next active phase:

1. Add reward and item-drop definitions.
2. Award currency and items transactionally after wins; draws and losses award
   nothing.
3. Add idempotency protection so a battle cannot be rewarded twice.
4. Add a minimal reward response and dashboard notification.
5. Add cat experience and a minimal level display if time allows.
6. Add battle and reward history.

**Exit criteria:** A win produces one persistent reward, which can be equipped
and used in a later battle.

### Phase 5 — Tiger Data marketplace

1. Add marketplace listings with seller, item, price, and status.
2. Add listing creation and cancellation.
3. Prevent selling equipped items.
4. Implement atomic purchase transactions with row locking or equivalent
   PostgreSQL safeguards.
5. Prevent expired, cancelled, already purchased, and self-invalidating
   purchases.
6. Add browsing and filtering by slot and rarity.
7. Add indexes based on actual active-listing queries.

**Exit criteria:** Two players can trade safely without duplicated items,
negative balances, or double purchases.

### Phase 6 — Asynchronous PvP

1. Add published build snapshots.
2. Let players publish their current equipment for challenges.
3. Reuse the PvE combat service for saved-build matches.
4. Store both participant snapshots and the result.
5. Add history and a small wins/rating leaderboard.

**Exit criteria:** An offline player can be challenged and can later view the
result.

### Phase 7 — Demo polish and Tiger Data analytics

1. Improve loading, empty, error, and pending-transaction states.
2. Add onboarding and a battle tutorial.
3. Add battle and marketplace metrics with PostgreSQL queries.
4. Add timestamped event data where time-series analysis is useful.
5. Add seed data and a repeatable demo script.
6. Add Docker and deployment documentation.

**Exit criteria:** A judge can complete the whole loop without assistance:
create player → equip cat → fight PvE → earn reward → trade gear → challenge a
saved build.

### Phase 8 — Solana integration

1. Add frontend wallet connection.
2. Issue backend nonces and verify signed wallet messages.
3. Associate verified wallet addresses with players.
4. Add an ownership interface with local and Solana implementations.
5. Mint selected rare gear as Solana assets.
6. Show mint and transaction links on item details.
7. Add on-chain settlement for selected marketplace items only if stable and
   time permits.

**Exit criteria:** Solana features are additive, optional, and do not break
database-backed gameplay for players without a wallet.

## Data model

Use definitions and instances separately. A definition describes an item type;
an instance is one owned, tradeable item.

| Table | Purpose |
|---|---|
| `players` | Development identity, display name, optional verified wallet |
| `cats` | Player cat, base sprite, level, experience |
| `currencies` | Current player balance and accounting metadata |
| `item_definitions` | Name, slot, rarity, sprite, base stats |
| `item_instances` | Owner, definition, rolled stats, state |
| `equipment` | Cat, slot, equipped item |
| `enemies` | Enemy stats, sprite, and difficulty |
| `battles` | Participants, seed, snapshots, result, status, timestamps |
| `battle_events` | Ordered events used to replay a battle |
| `rewards` | Battle, player, currency/item reward, claim state |
| `marketplace_listings` | Seller, item, price, status, timestamps |
| `build_snapshots` | Published equipment and stats for async PvP |

Use foreign keys, unique constraints for equipment slots, non-negative
currency constraints where practical, and transactions for rewards and
marketplace operations. Add indexes from observed API queries.

## API sequence

Implement API slices in phase order:

```text
GET  /health
POST /players
GET  /players/{player_id}
GET  /players/{player_id}/items
GET  /players/items/definitions
POST /players/{player_id}/cats/{cat_id}/items/{item_id}/equip
POST /players/{player_id}/cats/{cat_id}/items/{item_id}/unequip
POST /battles/pve
GET  /battles/{battle_id}
POST /marketplace/listings
GET  /marketplace/listings
POST /marketplace/listings/{listing_id}/purchase
POST /builds/{player_id}/publish
POST /pvp/challenges
```

Reserve wallet, nonce, minting, and blockchain transaction endpoints for
Phase 8.

## Engineering rules

- Build and verify one phase before starting the next.
- Keep combat server-authoritative and deterministic.
- Use explicit validation and clear API errors; do not silently fall back.
- Keep route handlers thin and put domain behavior in services.
- Keep the first art set small and use shared sprite dimensions.
- Prefer standard PostgreSQL SQL so Tiger Data remains easy to inspect.
- Do not add real-time networking; saved-build PvP is sufficient.
- Update this file's current-state checklist whenever a phase meaningfully
  changes.
