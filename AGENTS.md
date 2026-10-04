# Pixel Cat Arena Engineering Plan

This file is the working guide for implementing Pixel Cat Arena. Keep it
updated as each milestone is completed. `README.md` is the product-facing
description; this file contains implementation detail and agent guidance.

## Current implementation state

**Status:** Phase 0 scaffold complete; Tiger Cloud credentials and the first
migration are the next setup steps.

- [x] Product concept and MVP loop documented
- [x] Sequential implementation phases defined
- [x] Tiger Data selected as the production database foundation
- [x] Solana explicitly deferred until the local game is stable
- [x] Backend scaffold
- [x] Frontend scaffold
- [x] Tiger Data connection and health check
- [ ] Player and cat persistence
- [ ] Inventory and equipment
- [ ] Deterministic PvE
- [ ] Rewards and progression
- [ ] Marketplace
- [ ] Asynchronous PvP
- [ ] Hackathon polish and analytics
- [ ] Solana wallet and asset integration

The independent backend and frontend shells now exist. Frontend production
build and backend tests pass. The next task is to configure a real Tiger Cloud
`DATABASE_URL`, run the first migration, and then begin Phase 1. Do not skip
ahead to Solana or real-time multiplayer.

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

1. Create backend and frontend manifests.
2. Add environment loading and validate `DATABASE_URL` at startup.
3. Configure SQLAlchemy for Tiger Data PostgreSQL.
4. Add Alembic and create the baseline migration.
5. Add `GET /health` with an explicit database connectivity result.
6. Add a minimal Vite shell and backend API client.
7. Add local commands to run both services.
8. Document Tiger Cloud provisioning and environment setup.

**Exit criteria:** Both services start, the frontend calls the backend, and
`/health` verifies Tiger Data connectivity.

### Phase 1 — Player and cat

1. Add `players`, `cats`, and `currencies` tables.
2. Add a temporary development-player creation flow.
3. Seed one base cat and starter currency.
4. Add player and cat schemas, services, and routes.
5. Render the cat and basic HUD in Canvas.

**Exit criteria:** A new development player can refresh the app and see the
same cat and balance.

### Phase 2 — Items and equipment

1. Add item definitions and item instances.
2. Add common and rare seed data.
3. Add head, body, weapon, and accessory slots.
4. Store Attack, Defense, and Speed on item instances.
5. Enforce ownership, valid slots, and one item per equipped slot.
6. Add transparent PNG overlays with shared dimensions and anchors.
7. Add inventory and equip/unequip screens.

**Exit criteria:** Equipping a valid owned item changes both stats and the
visual cat, and the result survives a refresh.

### Phase 3 — Deterministic PvE

1. Add enemy definitions and initial enemy seed data.
2. Build a combat snapshot from cat and equipment.
3. Generate and persist a battle seed.
4. Resolve automatic turns in a backend combat service.
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
GET  /players/{player_id}/inventory
POST /cats/{cat_id}/equipment
DELETE /cats/{cat_id}/equipment/{slot}
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
