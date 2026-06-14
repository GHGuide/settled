import React from "react";

// Slack's own dark palette — kept realistic INSIDE the product window,
// which floats on the cream editorial background (Anthropic treatment).
const S = {
  bg: "#1A1D21",
  panel: "#222529",
  fg: "#E8E8E8",
  dim: "#9AA0A6",
  line: "#33373B",
  green: "#2EB67D",
  amber: "#ECB22E",
  gray: "#6B7177",
  sans: "'Inter', -apple-system, system-ui, sans-serif",
};

const AVA = ["#E0709A", "#7AA6E0", "#9B87D6", "#E0A85E", "#5EC2A8"];

const Avatar: React.FC<{ name: string; i?: number }> = ({ name, i = 0 }) => (
  <div style={{
    width: 40, height: 40, borderRadius: 9, flexShrink: 0,
    background: AVA[i % AVA.length], display: "flex", alignItems: "center",
    justifyContent: "center", color: "#1A1D21", fontWeight: 700, fontSize: 18,
    fontFamily: S.sans,
  }}>{name.trim().charAt(0)}</div>
);

const AppBadge = () => (
  <span style={{
    fontSize: 12, fontWeight: 700, color: S.dim, background: S.line,
    borderRadius: 4, padding: "1px 6px", marginLeft: 7, letterSpacing: 0.5,
  }}>APP</span>
);

export const Msg: React.FC<{ name: string; text: React.ReactNode; i?: number; app?: boolean; time?: string }> =
({ name, text, i = 0, app, time = "12:53" }) => (
  <div style={{ display: "flex", gap: 14, padding: "9px 26px", alignItems: "flex-start", fontFamily: S.sans }}>
    <Avatar name={name} i={i} />
    <div style={{ flex: 1 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
        <span style={{ fontWeight: 800, color: S.fg, fontSize: 20 }}>{name}</span>
        {app && <AppBadge />}
        <span style={{ color: S.dim, fontSize: 14, marginLeft: 3 }}>{time}</span>
      </div>
      <div style={{ color: S.fg, fontSize: 21, lineHeight: 1.45, marginTop: 2 }}>{text}</div>
    </div>
  </div>
);

export const Quote: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    borderLeft: `3px solid ${S.gray}`, paddingLeft: 14, margin: "7px 0",
    color: S.fg, fontSize: 20, lineHeight: 1.4,
  }}>{children}</div>
);

export const RatifyCard: React.FC<{ quote: string; conf: number; id: number }> = ({ quote, conf, id }) => (
  <div style={{ display: "flex", gap: 14, padding: "9px 26px", fontFamily: S.sans }}>
    <Avatar name="S" i={2} />
    <div style={{ flex: 1 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
        <span style={{ fontWeight: 800, color: S.fg, fontSize: 20 }}>Settled</span><AppBadge />
      </div>
      <div style={{ color: S.fg, fontSize: 20, marginTop: 3 }}>
        Looks like a decision — confidence <b style={{ color: S.green }}>{conf}%</b>. React ✅ to settle it.
      </div>
      <Quote>{quote}</Quote>
      <div style={{ color: S.dim, fontSize: 14 }}>source · ledger #{id} · 🟡 Proposed</div>
    </div>
  </div>
);

// A realistic Slack window that floats on the cream background.
export const SlackWindow: React.FC<{ channel?: string; children: React.ReactNode; w?: number; h?: number }> =
({ channel = "platform", children, w = 1280, h = 660 }) => (
  <div style={{
    width: w, height: h, background: S.bg, borderRadius: 18, overflow: "hidden",
    boxShadow: "0 40px 90px rgba(26,25,22,0.28), 0 8px 24px rgba(26,25,22,0.12)",
    border: `1px solid ${S.line}`, display: "flex", flexDirection: "column",
  }}>
    <div style={{ height: 46, background: S.panel, display: "flex", alignItems: "center",
      padding: "0 18px", gap: 8, borderBottom: `1px solid ${S.line}` }}>
      <div style={{ display: "flex", gap: 8 }}>
        {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
          <div key={c} style={{ width: 12, height: 12, borderRadius: 99, background: c }} />
        ))}
      </div>
      <div style={{ color: S.fg, fontWeight: 700, fontSize: 18, marginLeft: 14, fontFamily: S.sans }}># {channel}</div>
    </div>
    <div style={{ flex: 1, paddingTop: 12, overflow: "hidden" }}>{children}</div>
  </div>
);

export { S as SLACK };
