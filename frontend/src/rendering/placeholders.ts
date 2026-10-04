export function renderGlyph(visualKey: string): string {
  const glyphMap: Record<string, string> = {
    "woven-cap": "◐",
    "copper-vest": "▣",
    "pixel-sword": "⚔",
    "lucky-charm": "✦",
  };

  return glyphMap[visualKey] ?? "◫";
}
