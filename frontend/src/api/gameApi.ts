import { apiFetch } from "./client";
import type {
  BattleRead,
  EnemyProgressRead,
  EnemyRead,
  ItemInstanceRead,
  PlayerWithDetails,
  BuildSnapshotRead,
  PvpMatchRead,
  PvpChallengeRead,
  ListingRead,
  SaleResult,
} from "../types";

const STORAGE_KEY = "pixel-cat-arena:player-id";

export function getStoredPlayerId(): string | null {
  return window.localStorage.getItem(STORAGE_KEY);
}

export function setStoredPlayerId(playerId: string): void {
  window.localStorage.setItem(STORAGE_KEY, playerId);
}

export async function ensureDevPlayer(): Promise<PlayerWithDetails> {
  const savedId = getStoredPlayerId();

  if (savedId) {
    try {
      return await getPlayer(savedId);
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }

  const player = await apiFetch<PlayerWithDetails>("/dev/player", { method: "POST" });
  setStoredPlayerId(player.id);
  return player;
}

export async function getPlayer(playerId: string): Promise<PlayerWithDetails> {
  return apiFetch<PlayerWithDetails>(`/players/${playerId}`);
}

export async function getInventory(playerId: string): Promise<ItemInstanceRead[]> {
  return apiFetch<ItemInstanceRead[]>(`/players/${playerId}/items`);
}

export async function getCurrentEnemy(playerId: string): Promise<EnemyRead> {
  return apiFetch<EnemyRead>(`/battles/pve/current/${playerId}`);
}

export async function fightPve(playerId: string, enemyStage?: number): Promise<BattleRead> {
  return apiFetch<BattleRead>("/battles/pve", {
    method: "POST",
    body: JSON.stringify({ player_id: playerId, enemy_stage: enemyStage }),
  });
}

export async function getEnemyProgress(playerId: string): Promise<EnemyProgressRead> {
  return apiFetch<EnemyProgressRead>(`/battles/pve/enemies/${playerId}`);
}

export async function selectEnemyStage(playerId: string, stage: number): Promise<EnemyRead> {
  return apiFetch<EnemyRead>("/battles/pve/select", {
    method: "POST",
    body: JSON.stringify({ player_id: playerId, stage }),
  });
}

export async function equipItem(playerId: string, catId: string, itemId: string): Promise<ItemInstanceRead> {
  return apiFetch<ItemInstanceRead>(`/players/${playerId}/cats/${catId}/items/${itemId}/equip`, {
    method: "POST",
  });
}

export async function unequipItem(
  playerId: string,
  catId: string,
  itemId: string,
): Promise<ItemInstanceRead> {
  return apiFetch<ItemInstanceRead>(`/players/${playerId}/cats/${catId}/items/${itemId}/unequip`, {
    method: "POST",
  });
}

export function publishBuild(playerId: string): Promise<BuildSnapshotRead> {
  return apiFetch<BuildSnapshotRead>(`/builds/${playerId}/publish`, { method: "POST" });
}

export function challengePlayer(playerId: string, username: string): Promise<PvpChallengeRead> {
  return apiFetch<PvpChallengeRead>("/pvp/challenges", {
    method: "POST",
    body: JSON.stringify({ challenger_id: playerId, challenged_username: username }),
  });
}

export function resolveChallenge(challengeId: string): Promise<PvpMatchRead> {
  return apiFetch<PvpMatchRead>(`/pvp/challenges/${challengeId}/resolve`, { method: "POST" });
}

export function getPvpMatch(challengeId: string): Promise<PvpMatchRead> {
  return apiFetch<PvpMatchRead>(`/pvp/challenges/${challengeId}/match`);
}

export function getPvpHistory(playerId: string): Promise<PvpMatchRead[]> {
  return apiFetch<PvpMatchRead[]>(`/pvp/players/${playerId}/matches`);
}

export type ListingScope = "others" | "mine";

export function getListings(
  scope: ListingScope,
  filters: { slot?: string; rarity?: string } = {},
): Promise<ListingRead[]> {
  const params = new URLSearchParams({ scope });
  if (filters.slot) params.set("slot", filters.slot);
  if (filters.rarity) params.set("rarity", filters.rarity);
  return apiFetch<ListingRead[]>(`/marketplace/listings?${params.toString()}`);
}

export function createListing(itemId: string, price: number): Promise<ListingRead> {
  return apiFetch<ListingRead>("/marketplace/listings", {
    method: "POST",
    body: JSON.stringify({ item_id: itemId, price }),
  });
}

export function cancelListing(listingId: string): Promise<ListingRead> {
  return apiFetch<ListingRead>(`/marketplace/listings/${listingId}/cancel`, { method: "POST" });
}

export function purchaseListing(listingId: string): Promise<ListingRead> {
  return apiFetch<ListingRead>(`/marketplace/listings/${listingId}/purchase`, { method: "POST" });
}

export function sellItem(itemId: string): Promise<SaleResult> {
  return apiFetch<SaleResult>(`/players/items/${itemId}/sell`, { method: "POST" });
}

export function mintItemNft(itemId: string, walletAddress: string): Promise<ItemInstanceRead> {
  return apiFetch<ItemInstanceRead>(`/players/items/${itemId}/mint-nft`, {
    method: "POST",
    body: JSON.stringify({ wallet_address: walletAddress }),
  });
}

export function getClaimableItems(walletAddress: string): Promise<ItemInstanceRead[]> {
  const params = new URLSearchParams({ wallet_address: walletAddress });
  return apiFetch<ItemInstanceRead[]>(`/players/items/claimable?${params.toString()}`);
}

export function claimItemNft(
  mintAddress: string,
  walletAddress: string,
  signature: string,
): Promise<ItemInstanceRead> {
  return apiFetch<ItemInstanceRead>("/players/items/claim", {
    method: "POST",
    body: JSON.stringify({
      mint_address: mintAddress,
      wallet_address: walletAddress,
      signature,
    }),
  });
}
