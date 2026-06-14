// Anthropic-inspired warm/editorial palette. Cream bg, clay accent, serif display.
export const T = {
  bg: "#F2EFE7",        // warm cream
  bgElev: "#FBFAF5",    // lighter card
  bgDeep: "#E9E4D8",
  fg: "#1A1916",        // warm near-black
  dim: "#6B6660",       // warm gray
  faint: "#9C968C",
  clay: "#C9603A",      // Anthropic clay/coral accent
  clayLite: "#D97757",
  green: "#1F6F5C",     // muted settled green
  amber: "#B7791F",     // proposed/contested
  line: "#DBD5C7",
  serif: "'Fraunces', Georgia, 'Times New Roman', serif",
  sans: "'Inter', -apple-system, system-ui, sans-serif",
  mono: "'Roboto Mono', ui-monospace, 'SF Mono', Menlo, monospace",
};

export const STATUS = {
  proposed: { c: T.amber, dot: "●", label: "Proposed" },
  contested: { c: "#C0682A", dot: "●", label: "Contested" },
  settled: { c: T.green, dot: "●", label: "Settled" },
  superseded: { c: T.faint, dot: "○", label: "Superseded" },
  rejected: { c: "#A23B3B", dot: "●", label: "Rejected" },
} as const;
