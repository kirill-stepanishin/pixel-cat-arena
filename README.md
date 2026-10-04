# Pixel Cat Arena

Pixel Cat Arena is a browser game about raising a pixel-art cat, gearing it
up, and fighting your way through battles — solo or against other players.
Every fight, trade, and drop is resolved on the server, so your cat, your
gear, and your coins are always exactly what the game says they are.

## Play

- **Build your cat** — equip a body, head, weapon, and accessory from a
  pool of items across four rarities (common, rare, epic, legendary). Gear
  changes are visible on your cat instantly.
- **Fight** — battle an endless, scaling line of enemies for coins and item
  drops. Every fight is simulated the same way for everyone, with a full
  turn-by-turn playback.
- **Challenge other players** — publish your current build and challenge
  anyone by username. Matches are resolved on the server and watched back in
  the same arena.
- **Trade** — sell gear you don't need for coins, or list it on a
  player-run, fixed-price marketplace for others to buy.
- **Own your legendaries on Solana** — export a legendary item as a real
  Solana NFT without losing the ability to use it in battle. Selling or
  listing it in-game is permanently disabled once exported, because trading
  it is now a wallet-to-wallet transfer. Anyone who ends up holding that
  wallet can claim the item back into their own account with a free
  signature — no gas, no transaction required.

## Running it yourself

```text
cp .env.example .env
make install
make backend   # http://localhost:8000
make frontend  # http://localhost:5173
```

To play with a second account, use a second browser profile or an incognito
window (tabs in the same profile share a login cookie), and open
`http://localhost:5173` in both — not `127.0.0.1`.

Solana export/claim talks to Solana **devnet** and needs the
[Phantom wallet extension](https://phantom.app) to sign the free claim
message. No real funds are ever involved.

## Technology

Python/FastAPI/SQLAlchemy backend, TypeScript/Vite frontend, SQLite for local
data. See [`AGENTS.md`](AGENTS.md) for the implementation plan, data model,
API surface, and engineering guidance.
