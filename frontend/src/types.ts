export type SlotKey = "head" | "body" | "weapon" | "accessory";
export type StatKey = "attack" | "defense" | "speed";

export interface StatModifiers {
  attack: number;
  defense: number;
  speed: number;
}

export interface ItemDefinitionRead {
  id: string;
  name: string;
  slot: SlotKey;
  rarity: "common" | "rare" | "epic" | "legendary";
  visual_key: string;
  modifiers: StatModifiers;
  primary_stat: StatKey;
  primary_min: number;
  primary_max: number;
  bonus_stat_count: number;
  bonus_min: number;
  bonus_max: number;
  created_at: string;
}

export interface ItemInstanceRead {
  id: string;
  owner_id: string;
  item_definition_id: string;
  equipped_cat_id: string | null;
  created_at: string;
  modifiers: StatModifiers;
  definition: ItemDefinitionRead;
}

export interface CatRead {
  id: string;
  player_id: string;
  name: string;
  attack: number;
  defense: number;
  speed: number;
  created_at: string;
}

export interface CurrencyRead {
  id: string;
  player_id: string;
  currency_type: string;
  balance: number;
  created_at: string;
  updated_at: string;
}

export interface PlayerRead {
  id: string;
  username: string;
  created_at: string;
  updated_at: string;
}

export interface PlayerWithDetails extends PlayerRead {
  cats: CatRead[];
  currencies: CurrencyRead[];
}

export interface EnemyRead {
  id: string;
  stage: number;
  name: string;
  visual_key: string;
  attack: number;
  defense: number;
  speed: number;
}

export interface BattleRead {
  id: string;
  enemy_stage: number;
  result: "player" | "enemy";
  events: BattleEventRead[];
  player_snapshot: {
    name: string;
    attack: number;
    defense: number;
    speed: number;
    max_hp: number;
  };
  enemy_snapshot: {
    name: string;
    attack: number;
    defense: number;
    speed: number;
    max_hp: number;
  };
  reward: RewardRead | null;
}

export interface BattleEventRead {
  sequence: number;
  turn_number: number;
  event_type: "attack" | "victory" | "defeat";
  attacker: "player" | "enemy" | null;
  damage: number;
  player_hp: number;
  enemy_hp: number;
  elapsed_time: number;
}

export interface RewardRead {
  id: string;
  battle_id: string;
  player_id: string;
  currency_amount: number;
  item_instance_id: string | null;
}

export interface EnemyProgressRead {
  highest_unlocked_stage: number;
  selected_stage: number;
  enemies: EnemyRead[];
}
