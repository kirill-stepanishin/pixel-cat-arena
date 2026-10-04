# Pixel Cat Arena Engineering Plan

This file is the implementation guide for Pixel Cat Arena. `README.md` is the
product-facing overview; this file records the current state, boundaries, and
next work.

## Current implementation state

**Status:** Phases 0-8 are complete: accounts, PvE, async PvP, instant selling,
and the fixed-price marketplace all work locally. On the `solana-nft-prototype`
branch, legendary items can additionally be exported as real Solana devnet
NFTs and claimed back in-game by wallet signature (see Phase 10a below); this
has been manually verified end-to-end with a real Phantom wallet on devnet.
The next goal is Phase 9, the two-profile demo verification and targeted
polish. Public hosting is explicitly out of scope for this milestone.

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
- [x] Accounts and authenticated sessions (cookie sessions enforced on all player routes)
- [x] Instant item selling
- [x] Fixed-price marketplace
- [x] Asynchronous PvP (published builds, challenges, deterministic matches, shared arena playback)
- [ ] Local two-profile smoke test (separate profiles or incognito; tabs share a cookie)
- [x] Inventory/equipment/market UI polish (tooltips, comparisons, filters, toasts)
- [ ] Further visual polish and analytics
- [x] Solana NFT integration (devnet prototype on `solana-nft-prototype`
  branch: export legendary items as real NFTs, equip while minted, blocked
  resale, signature-based claim)

### What works now

Players register with a username and password (`POST /players` also signs in)
and authenticate with an HTTP-only `session_token` cookie; every player,
item, battle, build, PvP, and marketplace route requires it. Each player
starts with one cat named Mochi, base stats `12/10/8` for
attack/defense/speed, 125 starter coins, and four starter items. `/dev/player`
remains a hidden development helper.

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

The arena is a single screen with PvE and Async PvP tabs. Both play back
through the same battle animation with player stats on the left and opponent
stats on the right; the challenged cat is mirrored. Async PvP uses published
immutable build snapshots, a username challenge, and a server-resolved match;
no replay history is kept. Battle results appear in a result card with coin,
item, turn, and opponent plaques.

Items come from a data-driven pool (2 archetypes per slot, each at four
rarities) in `backend/app/content/items.py`. Each item has one primary stat
rolled from a rarity range, and higher rarities add bonus stats (see the
balance matrix in that file).

The backpack supports slot filtering and sorting, hover tooltips with roll
ranges, and stat comparison against the equipped item. Each card can equip,
quick-sell, or list. Quick-sell pays `total stats x rarity multiplier`
(common 1, rare 2, epic 3, legendary 5) and deletes the item in one
transaction; equipped and listed items cannot be sold. The marketplace is
fixed-price: a listing leaves the item in the seller's inventory but blocks
equipping and selling it; a purchase locks the listing, item, and both
currency rows, moves the coins and the item, and issues the buyer a new
instance number. Self-purchases, double purchases, and insufficient funds are
rejected, and buying needs a confirmation click.

On the `solana-nft-prototype` branch, a legendary item's card gains an
"⛓ Export" action that mints a real devnet NFT to a pasted wallet address
(Metaplex Token Metadata via `solana_bridge/mint-item-nft.mjs`, run as a Node
child process with a backend-held treasury keypair as fee/rent payer — the
player's wallet never needs devnet SOL or to sign the mint). The item stays
equippable and battle-usable after minting, but `sell` and `list` are
permanently blocked once `solana_mint_address` is set — item trading for that
instance moves on-chain. A "Claim from Solana" panel lets any player paste a
wallet address to see unclaimed items currently minted to it
(`check-holder.mjs` verifies live token-account ownership), then claim one by
signing a free `signMessage` challenge with Phantom (`frontend/src/solana/phantom.ts`)
— no transaction, no gas. The backend verifies the signature against the
claimed wallet and the on-chain holder before reassigning `owner_id`, so
in-game ownership always follows real on-chain NFT ownership without the
claimer needing to submit a transaction.

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
- Core gameplay (PvE, PvP, selling, marketplace) must never require a wallet
  or Solana connectivity; the Solana export/claim feature is strictly
  additive and only touches items the player opts to export.
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

### Phase 5 — Local accounts and sessions (complete)

1. [x] Add a password hash to players through a migration.
2. [x] Add register, login, current-user, and logout/session behavior.
3. [x] Use authenticated identity for protected player, item, battle, and currency
   operations instead of trusting arbitrary player IDs from the browser.
4. Keep scope small: no email verification, password reset, OAuth, or wallet
   login.

**Exit criteria:** Two players can register, log in, log out, and reload their
own independent cats, inventories, currency, and PvE progress from separate
browser tabs or profiles while sharing the same local backend and SQLite file.

### Phase 6 — Instant selling

1. [x] Add a server-side sale endpoint.
2. [x] Calculate value from rarity and rolled stats.
3. [x] Prevent selling equipped or listed items.
4. [x] Credit currency and remove the item in one transaction.
5. [x] Add frontend confirmation, price display, and refreshed inventory/balance.

**Exit criteria:** A player can sell an eligible item exactly once and receive
the server-calculated value.

### Phase 7 — Local fixed-price marketplace

1. [x] Add listing, seller, item, price, status, buyer, and timestamps.
2. [x] Add listing creation, active-listing browsing, cancellation, and purchase.
3. [x] Lock listing, item, and currency rows during purchase.
4. [x] Prevent self-purchases, double purchases, negative balances, and transfers
   of equipped or already listed items.
5. [x] Add filtering by slot and rarity.

**Exit criteria:** Two local accounts can list, browse, purchase, cancel, and
reconcile item ownership and currency without duplication or double spending.

### Phase 8 — Local asynchronous PvP

1. [x] Add immutable published build snapshots.
2. [x] Publish the current cat, equipment, and computed stats.
3. [x] Challenge another player by username or player ID.
4. [x] Reuse deterministic combat against the saved opponent snapshot.
5. [x] Persist both participant snapshots, seed, events, result, and timestamps.
6. [x] Add challenge/result status (replay history UI intentionally removed).

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

### Phase 10 — Future hosting, plus the Solana prototype

Public hosting, PostgreSQL migration, and broader wallet features (multi-chain
support, wallet-based login, marketplace priced in SOL) remain deferred and
are not required for the local demo.

The devnet NFT export/claim prototype itself is **done** on the
`solana-nft-prototype` branch (not yet merged to `main`):

1. [x] Add `solana_mint_address` / `solana_owner_wallet` columns to
   `item_instances` via migration.
2. [x] Add `solana_bridge/` Node scripts (`mint-item-nft.mjs`,
   `check-holder.mjs`) that mint real devnet NFTs (Metaplex Token Metadata)
   and verify live token-account ownership, invoked as subprocesses from
   `app/services/item_service.py`.
3. [x] Add `POST /players/items/{item_id}/mint-nft` (legendary-only, owner-only,
   blocks re-export) using a backend-held treasury keypair as fee/rent payer.
4. [x] Block `sell` and `marketplace/listings` for any item with a
   `solana_mint_address` set.
5. [x] Add `GET /players/items/claimable?wallet=...` (read-only holder lookup)
   and `POST /players/items/claim` (wallet-signature verified ownership
   transfer, no on-chain transaction from the claimer).
6. [x] Add frontend Export button/sub-panel, minted-item badge with Explorer
   link, and a "Claim from Solana" panel using a minimal Phantom
   `connect()`/`signMessage()` wrapper (`frontend/src/solana/phantom.ts`).
7. [x] Manually verified end-to-end on devnet with a real Phantom wallet:
   mint to a real address, confirm on Solana Explorer, claim from a second
   account via signature, confirm `owner_id` transferred while the mint
   address/wallet stayed intact.

If hosting is later requested, first migrate the database and test
marketplace concurrency before exposing the app publicly. Merging the Solana
branch to `main` and funding/documenting a longer-lived treasury keypair are
still open follow-ups.

## Data model

| Table | Purpose |
|---|---|
| `players` | Account identity, display name, and future password hash |
| `cats` | Player cat and base stats |
| `currencies` | Player balance |
| `item_definitions` | Static item type, slot, rarity, visual, and roll rules |
| `item_instances` | Owned item, rolled modifiers, equipment state, and (on `solana-nft-prototype`) `solana_mint_address`/`solana_owner_wallet` once exported |
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
```

On `solana-nft-prototype` only (devnet prototype, not merged to `main`):

```text
POST /players/items/{item_id}/mint-nft    export a legendary item as a devnet NFT
GET  /players/items/claimable?wallet=...  items currently minted to a wallet, claimable by anyone else
POST /players/items/claim                 wallet-signature verified ownership transfer
GET  /players/items/{item_id}/metadata.json  Metaplex-compatible metadata served by the backend
```

Remaining work is Phase 9 (demo verification and script) and the deferred
Phase 10; no new endpoints are planned.

## Engineering rules

- Build and verify one phase before starting the next.
- Prefer precise validation and explicit API errors.
- Never silently fall back on invalid ownership, balance, or battle state.
- Keep the client from choosing winners, rewards, prices, or transfer results.
- Keep SQLAlchemy and Alembic boundaries clean so a future PostgreSQL migration
  does not require a domain rewrite.
- Update this file's checklist whenever a phase meaningfully changes.
