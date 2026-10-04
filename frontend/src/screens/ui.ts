import type { ItemInstanceRead } from "../types";

type Slot = ItemInstanceRead["definition"]["slot"];
type Stat = "attack" | "defense" | "speed";

const STAT_LABEL: Record<Stat, string> = { attack: "ATK", defense: "DEF", speed: "SPD" };
const STATS: Stat[] = ["attack", "defense", "speed"];
const SLOT_ICON: Record<Slot, string> = { head: "🎩", body: "👕", weapon: "⚔️", accessory: "📿" };

export const uiContext: {
  balance: number;
  equippedBySlot: Map<string, ItemInstanceRead>;
} = { balance: 0, equippedBySlot: new Map() };

export function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char] as string
  ));
}

export function slotIcon(slot: Slot): string {
  return SLOT_ICON[slot] ?? "🎁";
}

export function statChips(item: ItemInstanceRead, compareTo?: ItemInstanceRead): string {
  const chips = STATS.filter((stat) => item.modifiers[stat] !== 0 || compareTo?.modifiers[stat]).map((stat) => {
    const value = item.modifiers[stat] || 0;
    const isPrimary = item.definition.primary_stat === stat;
    let delta = "";
    if (compareTo && compareTo.id !== item.id) {
      const diff = value - (compareTo.modifiers[stat] || 0);
      if (diff !== 0) delta = `<em class="${diff > 0 ? "up" : "down"}">${diff > 0 ? "▲" : "▼"}${Math.abs(diff)}</em>`;
    }
    return `<small class="${isPrimary ? "is-primary" : ""}">${STAT_LABEL[stat]} ${value}${delta}</small>`;
  });
  return chips.join("") || "<small>No stats</small>";
}

export function itemTip(item: ItemInstanceRead, extra = ""): string {
  const { definition } = item;
  const primary = definition.primary_stat;
  const rows = STATS.filter((stat) => item.modifiers[stat]).map((stat) => {
    const isPrimary = stat === primary;
    const range = isPrimary ? ` <span>(roll ${definition.primary_min}–${definition.primary_max})</span>` : ` <span>(bonus ${definition.bonus_min}–${definition.bonus_max})</span>`;
    return `<div>${STAT_LABEL[stat]} <b>${item.modifiers[stat]}</b>${range}</div>`;
  }).join("");
  return `<strong>${escapeHtml(definition.name)}</strong>
    <div class="tip-sub">${definition.rarity} ${definition.slot}</div>${rows}
    <div class="tip-sub">Quick-sell value: ${item.sell_price} coins</div>${extra}`;
}

export function tipAttr(html: string): string {
  return `data-tip="${escapeHtml(html)}"`;
}

export function toast(message: string, tone: "ok" | "error" | "info" = "info"): void {
  let host = document.querySelector<HTMLElement>("#toast-host");
  if (!host) {
    host = document.createElement("div");
    host.id = "toast-host";
    host.setAttribute("aria-live", "polite");
    document.body.append(host);
  }
  const node = document.createElement("div");
  node.className = `toast toast-${tone}`;
  node.textContent = message;
  host.append(node);
  window.setTimeout(() => {
    node.classList.add("is-leaving");
    window.setTimeout(() => node.remove(), 250);
  }, 3200);
}

export function initTooltips(): void {
  if (document.querySelector("#tooltip")) return;
  const tooltip = document.createElement("div");
  tooltip.id = "tooltip";
  tooltip.hidden = true;
  document.body.append(tooltip);

  const place = (event: MouseEvent): void => {
    const pad = 14;
    const { offsetWidth: w, offsetHeight: h } = tooltip;
    const x = Math.min(event.clientX + pad, window.innerWidth - w - 8);
    const y = event.clientY + pad + h > window.innerHeight ? event.clientY - h - pad : event.clientY + pad;
    tooltip.style.transform = `translate(${Math.max(8, x)}px, ${Math.max(8, y)}px)`;
  };

  document.addEventListener("mouseover", (event) => {
    const source = (event.target as HTMLElement).closest<HTMLElement>("[data-tip]");
    if (!source) {
      tooltip.hidden = true;
      return;
    }
    tooltip.innerHTML = source.dataset.tip ?? "";
    tooltip.hidden = false;
    place(event);
  });
  document.addEventListener("mousemove", (event) => {
    if (!tooltip.hidden) place(event);
  });
  document.addEventListener("click", () => { tooltip.hidden = true; });
}
