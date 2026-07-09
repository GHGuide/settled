import React from "react";
import { AbsoluteFill } from "remotion";
import { T } from "./theme";

const Box: React.FC<{ title: string; lines: string[]; accent?: string; w?: number }> =
({ title, lines, accent = T.line, w = 360 }) => (
  <div style={{
    width: w, background: "#FBFAF5", border: `2px solid ${accent}`, borderRadius: 18,
    padding: "22px 24px", boxShadow: "0 18px 44px rgba(26,25,22,0.10)",
  }}>
    <div style={{ fontFamily: T.serif, fontSize: 30, fontWeight: 600, color: T.fg }}>{title}</div>
    <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 7 }}>
      {lines.map((l, i) => (
        <div key={i} style={{ fontFamily: T.sans, fontSize: 20, color: T.dim, lineHeight: 1.3 }}>{l}</div>
      ))}
    </div>
  </div>
);

const Arrow: React.FC<{ label?: string }> = ({ label }) => (
  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", width: 110 }}>
    {label && <div style={{ fontFamily: T.sans, fontSize: 16, color: T.faint, marginBottom: 6, textAlign: "center", lineHeight: 1.2 }}>{label}</div>}
    <div style={{ color: T.clay, fontSize: 44, lineHeight: 1 }}>→</div>
  </div>
);

export const Architecture: React.FC = () => (
  <AbsoluteFill style={{
    background: `radial-gradient(120% 90% at 50% 15%, #FBFAF5 0%, ${T.bg} 55%, ${T.bgDeep} 100%)`,
    fontFamily: T.sans, padding: 80, justifyContent: "center",
  }}>
    <div style={{ textAlign: "center", marginBottom: 44 }}>
      <div style={{ color: T.faint, fontSize: 22, fontWeight: 600, letterSpacing: 5, textTransform: "uppercase" }}>Architecture</div>
      <div style={{ fontFamily: T.serif, fontSize: 64, fontWeight: 600, color: T.fg, marginTop: 8 }}>Settled</div>
    </div>

    <div style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <Box title="Slack" accent={T.line} w={335}
        lines={["#channels & threads", "/settled command", "App Home + Ratify/Details buttons", "Assistant (DM / @mention)", "human ✅ / ❌ ratify"]} />
      <Arrow label="messages · commands" />
      <div style={{ display: "flex", flexDirection: "column", gap: 18, alignItems: "center" }}>
        <Box title="Settled · Bolt app" accent={T.clay} w={430}
          lines={["extraction: noise-gate → LLM classifier", "confidence gate + human ✅ ratify (only a human settles)", "proposed → contested → settled → superseded", "signed supersede / contest edges"]} />
        <div style={{ color: T.dim, fontSize: 34 }}>↕</div>
        <Box title="SQLite ledger" accent={T.line} w={430}
          lines={["decisions · anchors (verbatim quote + permalink)", "edges · ratifications", "append-only hash-chained audit_log · verify_chain()"]} />
      </div>
      <Arrow label="same ledger" />
      <Box title="MCP server · decisions://" accent={T.green} w={355}
        lines={["is_binding(topic)", "query_decisions(q)", "verify_audit_log()", "resources · stdio + HTTP"]} />
      <Arrow label={"“is this still\nbinding?”"} />
      <Box title="External agents" accent={T.clay} w={300}
        lines={["Claude · IDE bots · CI", "check BEFORE acting", "→ stopped if superseded"]} />
    </div>

    <div style={{ textAlign: "center", marginTop: 44, fontFamily: T.sans, fontSize: 23, color: T.dim }}>
      Qualifying tech: our own MCP server (ungated). Retrieval tells you what was said — Settled tells you what still binds.
    </div>
    <div style={{ textAlign: "center", marginTop: 12, fontFamily: T.mono, fontSize: 18, color: T.faint }}>
      Python · Slack Bolt (Socket Mode) · SQLite · Model Context Protocol · OpenRouter (DeepSeek) · 29 tests + CI · live on Railway
    </div>
  </AbsoluteFill>
);
