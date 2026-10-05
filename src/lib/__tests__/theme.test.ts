import { PILLARS, contrastRatio, onAccent } from "../theme";

describe("contrastRatio", () => {
  it("matches known WCAG values", () => {
    expect(contrastRatio("#000000", "#FFFFFF")).toBeCloseTo(21, 0);
    expect(contrastRatio("#FFFFFF", "#FFFFFF")).toBeCloseTo(1, 5);
  });
});

describe("pillar label contrast", () => {
  const cases = Object.values(PILLARS).flatMap((p) => [
    [p.key, "light", p.light],
    [p.key, "dark", p.dark],
  ]);

  it.each(cases)("%s (%s) has readable text on its accent", (_key, _mode, accent) => {
    expect(contrastRatio(accent, onAccent(accent))).toBeGreaterThanOrEqual(3);
  });
});
