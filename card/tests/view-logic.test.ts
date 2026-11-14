import { describe, expect, it } from "vitest";
import { showsMediaControls, spellColor } from "../src/view-logic";

describe("showsMediaControls", () => {
  it("is true when at least one media player is configured", () => {
    expect(showsMediaControls(["media_player.bedroom"])).toBe(true);
    expect(
      showsMediaControls(["media_player.a", "media_player.b"]),
    ).toBe(true);
  });

  it("is false for a lights-only alarm (no players)", () => {
    expect(showsMediaControls([])).toBe(false);
  });

  it("is false when players is undefined", () => {
    expect(showsMediaControls(undefined)).toBe(false);
  });
});

describe("spellColor", () => {
  it.each([
    ["en", "Light color", "Light color"],
    [undefined, "Color temperature", "Color temperature"],
    ["en-GB", "Light color", "Light colour"],
    ["en-GB", "Color temperature", "Colour temperature"],
  ])("%s: %s -> %s", (language, text, expected) => {
    expect(spellColor(text, language)).toBe(expected);
  });
});
