# Pixel Cat Arena Engineering Plan

This file is the implementation guide for Pixel Cat Arena. `README.md` is the
product-facing overview; this file records the current state, boundaries, and
remaining work.

## Current implementation state

**Status:** The full local loop is complete and on `main`: accounts, PvE,
async PvP, instant selling, the fixed-price marketplace, and a Solana devnet
NFT export/claim prototype for legendary items. All of it has been manually
verified, including the Solana flow end-to-end with a real Phantom wallet on
devnet. Remaining work is a repeatable two-profile demo script and polish
(Phase 9) and anything hosting-related (Phase 10), both below. Public hosting
is explicitly out of scope for this milestone.

### What works now

Players register with a username and password (`POST /players` also signs in)
and authenticate with an HTTP-only `session_token` cookie; every player,
item, battle, build, PvP, and marketplace route requires it. Each player
starts with one cat named Mochi, base stats `12/10/8` for
attack/defense/speed, 125 starter coins, and four starter items.

The backend persists item definitions and rolled item modifiers separately.
Equipment is limited to one item per slot. Cat layers always render in this
order, regardless of API or equip order:

```text
base cat → body → accessory → head → weapon
```

PvE uses snapshots and a persisted seed. Turns are speed-based and
deterministic for a given snapshot and seed. Combat has no draw result: it
runs until a fighter reaches zero HP, and every attack deals at least one
damage after defense reduction. Victories grant stage-scaled coins and may
grant a deterministically selected item drop (`backend/app/services/battle_service.py`
rolls rarity before archetype; legendary odds are intentionally low — 2% by
default — so bump that constant locally if you need one on demand, e.g. for
a recording, and revert before committing). Duplicate item instances are
valid.

The arena is a single screen with PvE and Async PvP tabs, sharing one battle
animation with player stats on the left and opponent stats on the right.
Async PvP uses published immutable build snapshots, a username challenge,
and a server-resolved match; no replay history is kept.

Items come from a data-driven pool (2 archetypes per slot, each at four
rarities) in `backend/app/content/items.py`. The backpack supports slot
filtering and sorting, hover tooltips with roll ranges, and stat comparison
against the equipped item. Quick-sell pays `total stats x rarity multiplier`
(common 1, rare 2, epic 3, legendary 5); equipped and listed items can't be
sold. The marketplace is fixed-price: a listing blocks equipping/selling that
item; a purchase locks the listing, item, and both currency rows in one
transaction. Self-purchases, double purchases, and insufficient funds are
rejected.

A legendary item's card has an "⛓ Export" action that mints it as a real
Solana devnet NFT (Metaplex Token Metadata) to a pasted wallet address, via
`solana_bridge/mint-item-nft.mjs` run as a Node child process with a
backend-held treasury keypair paying fees/rent — the player's own wallet
never needs devnet SOL. The item stays equippable and battle-usable after
minting, but `sell` and `list` are permanently blocked once
`solana_mint_address` is set; further trading for that instance happens
on-chain. A "Claim from Solana" panel lets any player paste a wallet address
to see unclaimed items currently minted to it (`check-holder.mjs` verifies
live token-account ownership), then claim one by signing a free `signMessage`
challenge with Phantom (`frontend/src/solana/phantom.ts`) — no transaction,
no gas. The backend verifies the signature and the on-chain holder before
reassigning `owner_id`, so in-game ownership always follows real on-chain NFT
ownership without the claimer submitting a transaction.

## Technical stack

- Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Alembic
- TypeScript, Vite
- SQLite for local development; a PostgreSQL-compatible `DATABASE_URL` can be
  swapped in later without a domain rewrite
- Pytest and Vitest

```text
DATABASE_URL=sqlite+aiosqlite:///./pixel_cat_arena.db
```

The backend intentionally reports `503` from `/health` when the database is
missing or unavailable, making configuration failures explicit.

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
- Core gameplay (PvE, PvP, selling, marketplace) must never require a wallet
  or Solana connectivity; the Solana export/claim feature is strictly
  additive and only touches items the player opts to export.
- Do not build live networking; asynchronous saved-build PvP is sufficient.
- Do not add timed bidding before fixed-price trading is reliable.

## Remaining work

### Phase 9 — Local demo verification and targeted polish

1. Run one backend process, one frontend dev server, and the local SQLite
   database.
2. Open two profiles/incognito windows and register separate accounts.
3. Test PvE, item sale, listing, purchase, cancellation, asynchronous PvP,
   and the Solana export/claim flow from both accounts.
4. Keep a repeatable local demo script and reset procedure.

### Phase 10 — Future hosting

Public hosting, PostgreSQL migration, and broader wallet features
(multi-chain support, wallet-based login, marketplace priced in SOL) are
deferred and not required for the local demo. If hosting is later requested,
migrate the database and test marketplace concurrency before exposing the app
publicly, and plan for a longer-lived, funded treasury keypair instead of the
current local one.

## Data model

| Table | Purpose |
|---|---|
| `players` | Account identity, display name, password hash |
| `cats` | Player cat and base stats |
| `currencies` | Player balance |
| `item_definitions` | Static item type, slot, rarity, visual, and roll rules |
| `item_instances` | Owned item, rolled modifiers, equipment state, and `solana_mint_address`/`solana_owner_wallet` once exported |
| `enemies` | PvE enemy definitions |
| `battles` | Participants, seed, snapshots, result, and timestamps |
| `battle_events` | Ordered persisted combat events |
| `rewards` | Battle rewards and item drops |
| `marketplace_listings` | Fixed-price item listings and transfer state |
| `build_snapshots` | Immutable saved builds for asynchronous PvP |

Use foreign keys, unique constraints for equipment slots, non-negative
currency constraints where practical, and transactions for rewards, sales,
and marketplace operations.

## API surface

All routes except `/health` and `/auth/*` need the session cookie.

```text
GET  /health
POST /players                      register and sign in
POST /auth/register | /auth/login | /auth/logout
GET  /auth/me
GET  /players/{player_id}
GET  /players/{player_id}/items
GET  /players/items/definitions
POST /players/{player_id}/cats/{cat_id}/items/{item_id}/equip
POST /players/{player_id}/cats/{cat_id}/items/{item_id}/unequip
POST /players/items/{item_id}/sell
POST /battles/pve
GET  /battles/{battle_id}
GET  /battles/pve/current/{player_id}
GET  /battles/pve/enemies/{player_id}
GET  /battles/players/{player_id}/history
GET  /battles/players/{player_id}/rewards
POST /builds/{player_id}/publish
GET  /builds/{player_id}/published
POST /pvp/challenges
GET  /pvp/challenges/{challenge_id}
POST /pvp/challenges/{challenge_id}/resolve
GET  /pvp/challenges/{challenge_id}/match
GET  /pvp/players/{player_id}/challenges
GET  /pvp/players/{player_id}/matches
POST /marketplace/listings
GET  /marketplace/listings?scope=others|mine&slot=&rarity=
POST /marketplace/listings/{listing_id}/purchase
POST /marketplace/listings/{listing_id}/cancel
POST /players/items/{item_id}/mint-nft           export a legendary item as a devnet NFT
GET  /players/items/claimable?wallet=...         items minted to a wallet, claimable by anyone else
POST /players/items/claim                        wallet-signature verified ownership transfer
GET  /players/items/{item_id}/metadata.json      Metaplex-compatible metadata served by the backend
```

No new endpoints are currently planned; remaining work is Phase 9 and the
deferred Phase 10.

## Engineering rules

- Build and verify one phase before starting the next.
- Prefer precise validation and explicit API errors.
- Never silently fall back on invalid ownership, balance, or battle state.
- Keep the client from choosing winners, rewards, prices, or transfer results.
- Keep SQLAlchemy and Alembic boundaries clean so a future PostgreSQL migration
  does not require a domain rewrite.
- Update this file whenever the implementation state meaningfully changes.
