# Pixel Cat Arena

Pixel Cat Arena is a browser-based game about building a pixel-art cat,
collecting equipment, and fighting automatic battles. The current playable
slice is intentionally server-authoritative and focused on a reliable local
PvE loop.

## Current playable features

- Development-player provisioning through `POST /dev/player`
- Persistent player, cat, currency, item definition, and item instance data
- Four equipment slots: body, accessory, head, and weapon
- Server-validated equip and unequip actions
- Layered cat visuals in this order: `base cat → body → accessory → head → weapon`
- Computed attack, defense, and speed totals with equipment bonuses
- Infinite linearly scaled Dummy enemies
- Deterministic combat using persisted battle seeds and snapshots
- Combat continues until one side wins; defense cannot reduce damage below 1
- Persisted battle events, victory rewards, item drops, and enemy progression
- Timed battle playback with skip-to-result
- Inventory and equipment displays with rarity and stat modifiers

The frontend is a single-page TypeScript/Vite application. The backend is a
FastAPI application using SQLAlchemy, Alembic, and a configurable
SQLAlchemy-compatible database URL. SQLite is the current local development
database. A hosted PostgreSQL-compatible database can be selected later
without changing the domain model.

## Planned next features

1. Minimal accounts with username and securely hashed password or PIN
2. Authenticated player sessions
3. Instant item selling for server-calculated currency
4. Fixed-price marketplace listings, purchases, and cancellation
5. Asynchronous PvP against immutable published build snapshots
6. Inventory sorting, filtering, and comparison improvements
7. Deployment of the frontend and backend

Timed bidding auctions, live PvP, email-based account recovery, and Solana
NFTs are deferred until the core account, marketplace, and saved-build PvP
loop is stable.

## Technology

- Python 3.12
- FastAPI, Pydantic, SQLAlchemy 2, and Alembic
- TypeScript, Vite, HTML/CSS, and Canvas-compatible layered sprites
- SQLite for local development; PostgreSQL-compatible deployment is supported
- Pytest and Vitest

## Local development

```text
cp .env.example .env
make install
make backend
make frontend
make test
```

The backend runs on `http://localhost:8000` and the frontend on
`http://localhost:5173`. The backend reports `503` from `/health` until
`DATABASE_URL` is configured and the database can answer `SELECT 1`.

## Repository layout

```text
backend/
  app/
    api/
    models/
    schemas/
    services/
  migrations/
  tests/
frontend/
  src/
    api/
    rendering/
    screens/
    state/
  public/assets/
```

Keep authoritative rules in backend services. The frontend is responsible for
presentation, input, and animation; it must not determine battle winners,
rewards, ownership, sale prices, or marketplace transfers.

See [`AGENTS.md`](AGENTS.md) for implementation state, data model, API
sequence, and engineering guidance.
