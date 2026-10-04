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
  rarity: "common" | "rare";
  visual_key: string;
  modifiers: StatModifiers;
  created_at: string;
}

export interface ItemInstanceRead {
  id: string;
  owner_id: string;
  item_definition_id: string;
  equipped_cat_id: string | null;
  created_at: string;
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
