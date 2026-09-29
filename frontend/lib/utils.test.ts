import { describe, expect, it } from "vitest";

import { pct, scoreColor, truncate, SENTIMENT_COLORS } from "./utils";

describe("utils", () => {
  it("formats percentages", () => {
    expect(pct(91.44)).toBe("91%");
    expect(pct(91.44, 1)).toBe("91.4%");
  });

  it("maps scores to colors", () => {
    expect(scoreColor(85)).toContain("emerald");
    expect(scoreColor(70)).toContain("amber");
    expect(scoreColor(30)).toContain("rose");
  });

  it("truncates long text", () => {
    expect(truncate("short", 10)).toBe("short");
    expect(truncate("a".repeat(200), 50)).toHaveLength(51);
    expect(truncate("a".repeat(200), 50).endsWith("…")).toBe(true);
  });

  it("has a color per sentiment", () => {
    for (const key of ["Positive", "Negative", "Neutral", "Mixed"] as const) {
      expect(SENTIMENT_COLORS[key]).toMatch(/^#/);
    }
  });
});
