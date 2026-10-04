# Pixel Cat Arena

Pixel Cat Arena is a browser-based game about building a pixel-art cat,
collecting equipment, and fighting automatic battles. The current playable
slice is intentionally server-authoritative and focused on a reliable local
PvE loop.

## Current playable features

- Accounts: register, log in, and log out with cookie sessions
- Persistent players, cats, currency, item definitions, and item instances
- Data-driven item pool: two items per slot, each in four rarities, with one
  primary stat plus rarity-scaled bonus stats
- Four equipment slots (body, accessory, head, weapon) with server-validated
  equip/unequip and layered cat visuals
- Deterministic PvE against infinitely scaling Dummy enemies, with rewards,
  item drops, and animated playback
- Asynchronous PvP: publish your build, challenge another player by username,
  and watch the server-resolved match in the same arena
- Instant selling for a server-calculated coin value
- Fixed-price marketplace: list, browse, filter, buy, and cancel
- Backpack sorting and filtering, hover tooltips, and stat comparisons
- *(`solana-nft-prototype` branch)* Export legendary items as real Solana
  devnet NFTs, keep using them in battle, and claim another player's exported
  item into your own account with a free wallet-signature check — no gas, no
  on-chain transaction required from the claimer

The frontend is a single-page TypeScript/Vite application. The backend is a
FastAPI application using SQLAlchemy, Alembic, and a configurable
SQLAlchemy-compatible database URL. SQLite is the current local development
database. A hosted PostgreSQL-compatible database can be selected later
without changing the domain model.

## Playing with two accounts

Browser tabs in one profile share a login cookie, so use a second browser
profile or an incognito window for the second player, and use `localhost`
consistently (not `127.0.0.1`).

## Solana devnet prototype (`solana-nft-prototype` branch)

Core gameplay never requires a wallet. On this branch, a legendary item gains
an "⛓ Export" action that mints it as a real devnet NFT (Metaplex Token
Metadata) to any pasted Solana address; the backend's treasury keypair pays
all fees/rent, so the player's wallet needs no devnet SOL. The item keeps
working in battle, but selling and marketplace listing are permanently
blocked once exported — further trading happens on-chain. Any player can
paste a wallet address into the "Claim from Solana" panel to see items
currently minted to it, then claim one into their account by signing a free
message with Phantom (no transaction, no gas); the backend verifies the
signature and live on-chain holder before moving in-game ownership. This has
been manually verified end-to-end on devnet with a real Phantom wallet.

## Planned next features

1. A repeatable two-profile demo script and reset procedure
2. Further visual polish and analytics
3. Hosting with a PostgreSQL-compatible database (marketplace concurrency
   must be tested first)
4. Merge the Solana devnet prototype to `main` and document treasury-keypair
   provisioning for a longer-lived deployment

Timed bidding auctions, live PvP, and email-based account recovery are
deferred.

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
