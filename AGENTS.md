# Pixel Cat Arena Engineering Plan

This file is the working guide for implementing Pixel Cat Arena. Keep it
updated as each milestone is completed. `README.md` is the product-facing
description; this file contains implementation detail and agent guidance.

## Current implementation state

**Status:** Phase 1 player and cat persistence is complete; the Phase 2
inventory/equipment backend foundation is now in place. Frontend inventory
composition and visual overlays remain.

- [x] Product concept and MVP loop documented
- [x] Sequential implementation phases defined
- [x] Tiger Data selected as the production database foundation
- [x] Solana explicitly deferred until the local game is stable
- [x] Backend scaffold
- [x] Frontend scaffold
- [x] Tiger Data connection and health check
- [x] Player and cat persistence
- [ ] Inventory and equipment
- [ ] Deterministic PvE
- [ ] Rewards and progression
- [ ] Marketplace
- [ ] Asynchronous PvP
- [ ] Hackathon polish and analytics
- [ ] Solana wallet and asset integration

The independent backend and frontend shells now exist. Frontend production
build and backend tests pass. The next implementation stage is the frontend
completion of Phase 2: a single-page dashboard backed by the player and
inventory APIs. Tiger Cloud remains optional during local development; do not
skip ahead to Solana or real-time multiplayer.

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

Backend/frontend manifests, environment loading, SQLAlchemy, Alembic, the
health endpoint, Vite shell, and local commands are complete.

**Exit criteria:** Both services start and `/health` reports database status.

### Phase 1 — Player and cat

Player/cat/currency tables, starter data, schemas, services, routes, and the
validated stat model are complete. The frontend HUD is still placeholder-only.

**Exit criteria:** A development player persists with the same cat and balance.

### Phase 2 — Items and equipment

The backend foundation is complete: item definitions/instances, starter common
and rare items, four slots, structured stat modifiers, ownership validation,
and one equipped item per slot.

The next stage completes Phase 2 on the frontend:

1. On startup, call `POST /dev/player` and store the returned player ID in
   browser storage. Reuse that ID for subsequent loads.
2. Add separate API, state, rendering, and screen-composition modules.
3. Build one responsive page containing the cat, computed stats, four equipment
   slots, an arranged inventory, an enemy/NPC preview area, and a marketplace
   area that can later become a live view.
4. Use temporary CSS/Canvas placeholders for the cat and item visuals. Keep
   backend `visual_key` values stable so real transparent PNGs can replace them.
5. Display computed totals and bonuses, such as `ATK 15 (+3)`.
6. Treat `equipped_cat_id` returned by the server as authoritative; refresh
   inventory and stats after equip/unequip instead of relying on optimistic
   client state.
7. Include loading, empty, error, and pending-action states.

**Exit criteria:** Equipping a valid owned item changes both stats and the
placeholder visual composition, survives a refresh, and remains visible on the
single-page dashboard.

### Frontend product assumptions

- The MVP uses one page rather than separate inventory, marketplace, profile,
  and arena routes.
- The development player starts as `dev-player` with Mochi, 125 coins, and the
  four seeded starter items; this is temporary identity/data, not an auth
  design.
- The page presents the player's cat as the primary focus, with inventory,
  equipment, marketplace access, and the current enemy/NPC in the same view.
- The first enemy area is a placeholder for a future NPC and later PvP
  opponent; it is not interactive until the battle phase.
- The frontend automatically provisions the unauthenticated development player
  through `POST /dev/player` and stores the returned ID in browser storage.
- Placeholder visuals are intentional for now; no art asset pipeline is
  required before the next phase.
- Stat displays show both totals and equipment contributions.
- Server responses, not local guesses, define ownership and equipment state.

### Phase 3 — Deterministic PvE

1. Add enemy definitions and initial enemy seed data.
2. Build a combat snapshot from cat and equipment.
3. Generate and persist a battle seed.
4. Resolve automatic turns in a backend combat service using registered
   abilities/strategies for special cat and enemy behavior.
5. Persist the winner and ordered battle events.
6. Add the battle API and Canvas replay.
7. Test damage, speed/turn order, victory, defeat, and edge cases.

Start with:

```text
damage = max(1, attacker_attack - defender_defense / 2)
turn_interval = base_interval / speed_multiplier
```

**Exit criteria:** Identical snapshots and seeds always produce identical
results. The client cannot select the winner or reward.

### Phase 4 — Rewards and progression

1. Add reward and item-drop definitions.
2. Award currency and items transactionally after wins.
3. Add idempotency protection for reward claims.
4. Add cat experience and a minimal level display if time allows.
5. Add battle and reward history.

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
