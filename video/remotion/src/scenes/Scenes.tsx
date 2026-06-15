import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate, OffthreadVideo, staticFile } from "remotion";
import { T, STATUS } from "../theme";
import { Msg, RatifyCard, Quote, SlackWindow } from "../components/Slack";
import { CameraRig, Cam } from "../CameraRig";

const Cream: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{
    fontFamily: T.sans,
    background: `radial-gradient(120% 90% at 50% 18%, #FBFAF5 0%, ${T.bg} 52%, ${T.bgDeep} 100%)`,
  }}>{children}</AbsoluteFill>
);

// calm, slow entrance
const useRise = (delay = 0, dur = 26) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f - delay, fps, config: { damping: 200, mass: 1.1 }, durationInFrames: dur });
  return { o: s, y: interpolate(s, [0, 1], [22, 0]) };
};

// slow continuous Ken-Burns zoom/pan — fixed long ramp so motion is always gentle
// (scenes are shorter than the ramp, so they only ever use the slow early part)
const useKen = (toScale = 1.08, toY = -26, span = 560) => {
  const f = useCurrentFrame();
  const scale = interpolate(f, [0, span], [1.0, toScale], { extrapolateRight: "clamp" });
  const y = interpolate(f, [0, span], [0, toY], { extrapolateRight: "clamp" });
  return { scale, y };
};

// muted eyebrow (gray) — accent reserved for one key word in the headline
const Eyebrow: React.FC<{ children: React.ReactNode; o?: number }> = ({ children, o = 1 }) => (
  <div style={{ opacity: o, color: T.faint, fontFamily: T.sans, fontSize: 20, fontWeight: 600,
    letterSpacing: 4, textTransform: "uppercase" }}>{children}</div>
);
// accent a key word in a headline
const A: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span style={{ color: T.clay }}>{children}</span>
);

const Headline: React.FC<{ children: React.ReactNode; size?: number; style?: React.CSSProperties }> =
({ children, size = 78, style }) => (
  <div style={{ fontFamily: T.serif, fontWeight: 600, fontSize: size, color: T.fg,
    lineHeight: 1.08, letterSpacing: -1, ...style }}>{children}</div>
);

const Caption: React.FC<{ children: React.ReactNode; o?: number }> = ({ children, o = 1 }) => (
  <div style={{ opacity: o, fontFamily: T.sans, fontSize: 28, color: T.dim, lineHeight: 1.5 }}>{children}</div>
);

// ---------------------------------------------------------------- s01 hook — guardrail cold-open
// Leads with the differentiator: an agent about to act on a reversed decision, stopped by Settled.
export const Hook: React.FC = () => {
  const { fps } = useVideoConfig();
  const f = useCurrentFrame();
  // reveal delays synced to the 20.6s VO beats
  const eyebrow = useRise(2), card = useRise(8);
  const lineA = useRise(100);   // "...build on Postgres"
  const lineB = useRise(215);   // "it checks Settled"
  const interceptO = useRise(270).o;  // "Superseded..."
  const interceptPop = spring({ frame: f - 270, fps, config: { damping: 12, mass: 0.8 } });
  const redFlash = interpolate(f, [270, 285, 320], [0, 0.16, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const lineC = useRise(385);   // "the agent fixes itself"
  const tag = useRise(470);     // "That's Settled..."
  const row: React.CSSProperties = { fontFamily: T.mono, fontSize: 27, lineHeight: 1.5, color: "#E8E8E8" };
  return (
    <Cream>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 90 }}>
        <div style={{ opacity: eyebrow.o, marginBottom: 22 }}><Eyebrow>An agent, about to act</Eyebrow></div>
        <div style={{ position: "relative", opacity: card.o, transform: `translateY(${card.y}px)`,
          width: 1200, background: "#1A1D21", borderRadius: 20, border: "1px solid #33373B",
          boxShadow: "0 50px 110px rgba(26,25,22,0.30)", padding: "42px 48px", overflow: "hidden" }}>
          <AbsoluteFill style={{ background: `rgba(224,30,90,${redFlash})`, pointerEvents: "none" }} />
          {/* agent intends to act on the old decision */}
          <div style={{ ...row, opacity: lineA.o }}>
            <span style={{ color: "#7AA6E0" }}>agent</span> <span style={{ color: "#9AA0A6" }}>deploy →</span> provision datastore: <b style={{ color: "#E0A85E" }}>Postgres</b>
          </div>
          {/* checks Settled first */}
          <div style={{ ...row, opacity: lineB.o, marginTop: 16, color: "#9AA0A6" }}>
            ↳ asks Settled&nbsp;&nbsp;<span style={{ color: "#E8E8E8" }}>is_binding(</span><span style={{ color: "#5EC2A8" }}>"datastore"</span><span style={{ color: "#E8E8E8" }}>)</span>
          </div>
          {/* intercept — superseded */}
          <div style={{ opacity: interceptO, transform: `scale(${0.96 + interceptPop * 0.04})`, transformOrigin: "left center",
            marginTop: 22, padding: "18px 22px", borderRadius: 14, background: "#241A1D", border: "1px solid rgba(224,30,90,0.5)" }}>
            <div style={{ ...row, color: "#FF6B8A", fontWeight: 700 }}>⛔ SUPERSEDED — Postgres no longer binds</div>
            <div style={{ ...row, marginTop: 8 }}>→ datastore is <b style={{ color: "#2EB67D" }}>Aurora</b> now&nbsp;&nbsp;<span style={{ color: "#9AA0A6", fontSize: 21 }}>settledco.slack.com/…/p1781 · permalink</span></div>
          </div>
          {/* agent rewrites its own code (the real demo's punchline) */}
          <div style={{ opacity: lineC.o, marginTop: 22 }}>
            <div style={{ ...row, color: "#2EB67D" }}>
              <span style={{ color: "#7AA6E0" }}>agent</span> rewrites <b>0007_create_datastore.sql</b> → Aurora ✓
            </div>
            <div style={{ ...row, fontSize: 22, marginTop: 6 }}>
              <span style={{ color: "#FF6B8A" }}>- conn: pg-primary.internal</span>
              &nbsp;&nbsp;&nbsp;<span style={{ color: "#2EB67D" }}>+ conn: …cluster.rds.amazonaws.com</span>
            </div>
          </div>
        </div>
        <div style={{ marginTop: 42, textAlign: "center", opacity: tag.o, transform: `translateY(${tag.y}px)`, maxWidth: 1200 }}>
          <Headline size={50}>Settled — the decision layer agents check <A>before they act.</A></Headline>
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// ------------------------------------------------------------- s02 problem
const THREAD = [
  { n: "Dana Whitfield", t: "Let's go with Postgres for the primary datastore.", d: "Apr 13", i: 0 },
  { n: "Sam Okafor", t: "Final call: we're going with MongoDB — the document model fits.", d: "Apr 28", i: 1 },
  { n: "Dana Whitfield", t: "Decision: we'll use Aurora as the primary datastore.", d: "May 23", i: 0 },
];
export const Problem: React.FC = () => {
  const f = useCurrentFrame();
  const head = useRise(6);
  const ken = useKen(1.05, 0);
  const scroll = interpolate(f, [30, 130], [0, -60], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Cream>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", padding: "0 90px", gap: 70 }}>
        <div style={{ width: 540, opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>The problem</Eyebrow>
          <Headline size={66} style={{ marginTop: 22 }}>Three weeks later, which decision still binds?</Headline>
          <div style={{ marginTop: 28 }}><Caption>The thread scrolls away. A teammate — or an agent — acts on the wrong one.</Caption></div>
        </div>
        <div style={{ flex: 1, display: "flex", justifyContent: "center", transform: `scale(${ken.scale})` }}>
          <SlackWindow channel="platform" w={760} h={560}>
            <div style={{ transform: `translateY(${scroll}px)` }}>
              {THREAD.map((m, k) => {
                const a = useRise(16 + k * 18);
                return (
                  <div key={k} style={{ opacity: a.o, transform: `translateY(${a.y}px)` }}>
                    <Msg name={m.n} i={m.i} time={m.d} text={m.t} />
                  </div>
                );
              })}
            </div>
          </SlackWindow>
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// ------------------------------------------------------------- s03 capture
export const Capture: React.FC = () => {
  const head = useRise(6), msg = useRise(20), reply = useRise(52);
  const ken = useKen(1.07, -20);
  return (
    <Cream>
      <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", padding: "70px 90px" }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>Capture</Eyebrow>
          <Headline size={56} style={{ marginTop: 16 }}>It catches the decision, and asks a human.</Headline>
        </div>
        <div style={{ marginTop: 40, transform: `scale(${ken.scale}) translateY(${ken.y}px)` }}>
          <SlackWindow channel="platform" w={1180} h={440}>
            <div style={{ opacity: msg.o, transform: `translateY(${msg.y}px)` }}>
              <Msg name="Leonardo C." i={4} text="Final call: we're standardizing on GitHub Actions for CI across all repos." />
            </div>
            <div style={{ opacity: reply.o, transform: `translateY(${reply.y}px)`, marginTop: 6 }}>
              <RatifyCard quote="Final call: we're standardizing on GitHub Actions for CI across all repos." conf={98} id={15} />
            </div>
          </SlackWindow>
        </div>
        <div style={{ marginTop: 28 }}><Caption o={useRise(76).o}>Precision first — if it isn't sure, it stays silent.</Caption></div>
      </AbsoluteFill>
    </Cream>
  );
};

// -------------------------------------------------------------- s04 ratify
export const Ratify: React.FC = () => {
  const { fps } = useVideoConfig();
  const f = useCurrentFrame();
  const pop = spring({ frame: f - 12, fps, config: { damping: 14, mass: 0.9 } });
  const txt = useRise(38);
  return (
    <Cream>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center" }}>
        <div style={{ transform: `scale(${pop})`, fontSize: 170 }}>✅</div>
        <Headline size={92} style={{ marginTop: 18, color: T.green, opacity: txt.o, transform: `translateY(${txt.y}px)` }}>Settled.</Headline>
        <div style={{ marginTop: 18 }}><Caption o={txt.o}>The human stays in the loop — that's the feature.</Caption></div>
      </AbsoluteFill>
    </Cream>
  );
};

// ----------------------------------------------------------- s05 lifecycle
const LIFE = [
  { label: "Postgres", status: "superseded" as const, d: "Apr 13" },
  { label: "MongoDB", status: "superseded" as const, d: "Apr 28" },
  { label: "Aurora", status: "settled" as const, d: "May 23" },
];
export const Lifecycle: React.FC = () => {
  const head = useRise(4);
  return (
    <Cream>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 90 }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>Epistemic status</Eyebrow>
          <Headline size={58} style={{ marginTop: 16 }}>Every decision carries a status.</Headline>
        </div>
        <div style={{ display: "flex", alignItems: "center", marginTop: 80 }}>
          {LIFE.map((s, k) => {
            const a = useRise(24 + k * 24, 22);
            const st = STATUS[s.status];
            return (
              <React.Fragment key={k}>
                <div style={{ opacity: a.o, transform: `translateY(${a.y}px)`, textAlign: "center", width: 320 }}>
                  <div style={{ fontFamily: T.serif, fontSize: 50, fontWeight: 600, color: s.status === "settled" ? T.green : T.faint }}>{s.label}</div>
                  <div style={{ marginTop: 14, color: st.c, fontFamily: T.sans, fontSize: 22, fontWeight: 600, letterSpacing: 1 }}>
                    {st.dot} {st.label}
                  </div>
                  <div style={{ marginTop: 8, color: T.faint, fontSize: 20, fontFamily: T.sans }}>{s.d}</div>
                </div>
                {k < LIFE.length - 1 && (
                  <div style={{ opacity: useRise(40 + k * 24).o, color: T.clay, fontSize: 46, margin: "0 -10px" }}>→</div>
                )}
              </React.Fragment>
            );
          })}
        </div>
        <div style={{ marginTop: 70 }}><Caption o={useRise(90).o}>Anchored to the exact words and a permalink. Never a paraphrase.</Caption></div>
      </AbsoluteFill>
    </Cream>
  );
};

// ------------------------------------------------- difference ("what others can't")
export const Difference: React.FC = () => {
  const head = useRise(2), l = useRise(20), r = useRise(40), line = useRise(64);
  return (
    <Cream>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 90 }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>What others can't do</Eyebrow>
          <Headline size={58} style={{ marginTop: 14 }}>Other tools log decisions. <A>Settled answers agents.</A></Headline>
        </div>
        <div style={{ display: "flex", gap: 40, marginTop: 64, alignItems: "stretch" }}>
          <div style={{ opacity: l.o, transform: `translateY(${l.y}px)`, width: 560, padding: 40,
            borderRadius: 20, background: "#FBFAF5", border: `1px solid ${T.line}` }}>
            <div style={{ fontFamily: T.sans, fontSize: 20, fontWeight: 700, color: T.faint, letterSpacing: 1 }}>EVERY OTHER DECISION TOOL</div>
            <div style={{ fontFamily: T.serif, fontSize: 38, color: T.dim, marginTop: 14, lineHeight: 1.2 }}>Logs a decision for a <i>person</i> to read later.</div>
            <div style={{ fontFamily: T.sans, fontSize: 22, color: T.faint, marginTop: 18 }}>📝 A searchable record. Humans only.</div>
          </div>
          <div style={{ opacity: r.o, transform: `translateY(${r.y}px)`, width: 560, padding: 40,
            borderRadius: 20, background: "#fff", border: `2px solid ${T.clay}`,
            boxShadow: "0 30px 70px rgba(201,96,58,0.16)" }}>
            <div style={{ fontFamily: T.sans, fontSize: 20, fontWeight: 700, color: T.clay, letterSpacing: 1 }}>SETTLED</div>
            <div style={{ fontFamily: T.serif, fontSize: 38, color: T.fg, marginTop: 14, lineHeight: 1.2 }}>Answers the <i>agent</i> — before it acts.</div>
            <div style={{ fontFamily: T.sans, fontSize: 22, color: T.fg, marginTop: 18 }}>🤖 “Is this still binding?” → yes/no + the source.</div>
          </div>
        </div>
        <div style={{ marginTop: 50, opacity: line.o }}>
          <Caption>So an agent never acts on a decision the team already reversed.</Caption>
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// ---------------------------------------------------------------- s06 mcp
export const Mcp: React.FC = () => {
  const head = useRise(4), call = useRise(26), resp = useRise(56), hi = useRise(84);
  const codeBox: React.CSSProperties = {
    background: "#FBFAF5", border: `1px solid ${T.line}`, borderRadius: 18, padding: 38,
    fontFamily: T.mono, fontSize: 25, lineHeight: 1.65, color: T.fg,
    maxWidth: 1280, margin: "0 auto", boxShadow: "0 24px 60px rgba(26,25,22,0.10)",
    whiteSpace: "pre",
  };
  return (
    <Cream>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 90 }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)`, marginBottom: 40 }}>
          <Eyebrow>The MCP server — decisions://</Eyebrow>
          <Headline size={56} style={{ marginTop: 16 }}>Any agent can ask: is this still binding?</Headline>
        </div>
        <div style={codeBox}>
          <div style={{ opacity: call.o, color: T.dim }}>
            <span style={{ color: T.clay }}>claude</span> → mcp.call(<span style={{ color: T.green }}>"is_binding"</span>, {"{ topic: "}<span style={{ color: T.green }}>"datastore"</span>{" }"})
          </div>
          <div style={{ opacity: resp.o, marginTop: 16 }}>
{`{
  "binding": `}<span style={{ color: T.green }}>true</span>{`,
  "statement": `}<span style={{ background: hi.o > 0.5 ? "#1F6F5C22" : "transparent", borderRadius: 4 }}>"Move primary datastore to Aurora"</span>{`,
  "permalink": "settledco.slack.com/…/p1781…"
}`}
          </div>
        </div>
        <div style={{ marginTop: 44 }}>
          <div style={{ opacity: hi.o, fontFamily: T.serif, fontSize: 38, fontWeight: 600, color: T.clay, textAlign: "center" }}>
            The guardrail for every agent in the workspace.
          </div>
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// -------------------------------------------------------------- s07 close
export const Close: React.FC = () => {
  const a = useRise(6), b = useRise(30), c = useRise(56);
  return (
    <Cream>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center", padding: 120 }}>
        <div style={{ opacity: a.o, transform: `translateY(${a.y}px)`, maxWidth: 1300 }}>
          <Headline size={52} style={{ fontWeight: 500, lineHeight: 1.3 }}>
            Retrieval tells you what was <span style={{ color: T.dim, fontStyle: "italic" }}>said</span>.<br />
            Settled tells you what was <span style={{ color: T.clay }}>decided</span> — and whether it still binds.
          </Headline>
        </div>
        <Headline size={130} style={{ marginTop: 64, opacity: b.o }}>Settled</Headline>
        <div style={{ marginTop: 20, opacity: c.o }}><Caption>The shared source of truth for humans and agents in Slack.</Caption></div>
      </AbsoluteFill>
    </Cream>
  );
};

// --------------------------------------------------------- s03 split-screen (dramatic)
const Banner: React.FC<{ kind: "bad" | "good"; children: React.ReactNode; o: number; pop: number }> =
({ kind, children, o, pop }) => (
  <div style={{
    opacity: o, transform: `scale(${pop})`, margin: "14px 18px 0", padding: "14px 18px",
    borderRadius: 12, fontFamily: T.sans, fontSize: 19, fontWeight: 700, textAlign: "center",
    color: kind === "bad" ? "#E01E5A" : "#2EB67D",
    background: kind === "bad" ? "rgba(224,30,90,0.12)" : "rgba(46,182,125,0.12)",
    border: `1px solid ${kind === "bad" ? "rgba(224,30,90,0.5)" : "rgba(46,182,125,0.5)"}`,
  }}>{children}</div>
);

// compact message for the dense side-by-side
const MiniMsg: React.FC<{ name: string; text: React.ReactNode; i?: number; app?: boolean; time?: string; o?: number }> =
({ name, text, i = 0, app, time, o = 1 }) => (
  <div style={{ opacity: o, display: "flex", gap: 11, padding: "6px 20px", alignItems: "flex-start", fontFamily: "'Inter',sans-serif" }}>
    <div style={{ width: 30, height: 30, borderRadius: 7, flexShrink: 0, background: ["#E0709A","#7AA6E0","#9B87D6","#E0A85E","#5EC2A8"][i%5], display: "flex", alignItems: "center", justifyContent: "center", color: "#1A1D21", fontWeight: 700, fontSize: 14 }}>{name.charAt(0)}</div>
    <div style={{ flex: 1 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontWeight: 800, color: "#E8E8E8", fontSize: 15 }}>{name}</span>
        {app && <span style={{ fontSize: 10, fontWeight: 700, color: "#9AA0A6", background: "#33373B", borderRadius: 3, padding: "0 5px" }}>APP</span>}
        {time && <span style={{ color: "#9AA0A6", fontSize: 12 }}>{time}</span>}
      </div>
      <div style={{ color: "#E8E8E8", fontSize: 15.5, lineHeight: 1.4, marginTop: 1 }}>{text}</div>
    </div>
  </div>
);

export const Split: React.FC = () => {
  const { fps } = useVideoConfig();
  const f = useCurrentFrame();
  const head = useRise(4), cols = useRise(14);
  // staggered message reveals (shared decisions early, divergence late)
  const r = (d: number) => useRise(d).o;
  const bannerL = useRise(250), bannerR = useRise(265);
  const popL = spring({ frame: f - 250, fps, config: { damping: 11, mass: 0.8 } });
  const popR = spring({ frame: f - 265, fps, config: { damping: 11, mass: 0.8 } });
  const redWash = interpolate(f, [250, 290], [0, 0.10], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const greenGlow = interpolate(f, [265, 300], [0, 0.08], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Cream>
      <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", padding: "30px 50px" }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>Same conversation, two teams</Eyebrow>
          <Headline size={44} style={{ marginTop: 8 }}>One ships an incident. The other ships clean.</Headline>
        </div>
        <div style={{ display: "flex", gap: 36, marginTop: 22, alignItems: "flex-start", opacity: cols.o }}>
          {/* WITHOUT */}
          <div style={{ textAlign: "center", position: "relative" }}>
            <div style={{ color: T.faint, fontFamily: T.sans, fontSize: 19, fontWeight: 700, letterSpacing: 2, marginBottom: 8 }}>WITHOUT SETTLED</div>
            <div style={{ position: "relative", borderRadius: 16, overflow: "hidden" }}>
              <SlackWindow channel="platform" w={660} h={560}>
                <MiniMsg name="Dana Whitfield" i={0} time="Apr 13" o={r(24)} text="Let's go with Postgres for the datastore." />
                <MiniMsg name="Sam Okafor" i={1} time="Apr 28" o={r(46)} text="Change of plan — final call, we're on MongoDB." />
                <MiniMsg name="Dana Whitfield" i={0} time="May 23" o={r(70)} text="Update: moving to Aurora. Postgres & Mongo are out." />
                <MiniMsg name="Jordan Reyes" i={3} time="Jun 12" o={r(150)} text="starting the data migration — Postgres, per the April thread 🚀" />
                <MiniMsg name="Priya Nair" i={2} time="Jun 12" o={r(185)} text="wait… didn't we move off Postgres? 😳" />
                <MiniMsg name="Jordan Reyes" i={3} time="Jun 12" o={r(220)} text="can't find where we decided… rebuilding on Aurora now 😖" />
              </SlackWindow>
              <AbsoluteFill style={{ background: `rgba(224,30,90,${redWash})`, pointerEvents: "none" }} />
            </div>
            <Banner kind="bad" o={bannerL.o} pop={popL}>⚠️ 3 days lost — built on a reversed decision</Banner>
          </div>
          {/* WITH */}
          <div style={{ textAlign: "center", position: "relative" }}>
            <div style={{ color: T.green, fontFamily: T.sans, fontSize: 19, fontWeight: 700, letterSpacing: 2, marginBottom: 8 }}>WITH SETTLED</div>
            <div style={{ position: "relative", borderRadius: 16, overflow: "hidden" }}>
              <SlackWindow channel="platform" w={660} h={560}>
                <MiniMsg name="Dana Whitfield" i={0} time="Apr 13" o={r(24)} text="Let's go with Postgres for the datastore." />
                <MiniMsg name="Sam Okafor" i={1} time="Apr 28" o={r(46)} text="Change of plan — final call, we're on MongoDB." />
                <MiniMsg name="Dana Whitfield" i={0} time="May 23" o={r(70)} text="Update: moving to Aurora. Postgres & Mongo are out." />
                <MiniMsg name="Settled" i={2} app time="May 23" o={r(96)} text={<span>🟢 <b style={{ color: "#2EB67D" }}>Settled</b> — Aurora binding · Postgres, Mongo superseded</span>} />
                <MiniMsg name="Jordan Reyes" i={3} time="Jun 12" o={r(150)} text="starting the migration — checking Settled first" />
                <MiniMsg name="Jordan Reyes" i={3} time="Jun 12" o={r(200)} text={<span>agent: <b>is_binding</b>(datastore) → <b>Aurora</b>. on the right one ✅</span>} />
              </SlackWindow>
              <AbsoluteFill style={{ background: `rgba(46,182,125,${greenGlow})`, pointerEvents: "none" }} />
            </div>
            <Banner kind="good" o={bannerR.o} pop={popR}>✅ Shipped right the first time — zero rework</Banner>
          </div>
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// --------------------------------------------------------- s06 contested
export const Contested: React.FC = () => {
  const head = useRise(4), w = useRise(18), note = useRise(56);
  const ken = useKen(1.05, -12);
  return (
    <Cream>
      <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", padding: "70px 90px" }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>When it isn't decided</Eyebrow>
          <Headline size={56} style={{ marginTop: 14 }}>Settled says so. Nothing binds without a human.</Headline>
        </div>
        <div style={{ marginTop: 38, transform: `scale(${ken.scale}) translateY(${ken.y}px)`, opacity: w.o }}>
          <SlackWindow channel="platform" w={1120} h={420}>
            <Msg name="Priya Nair" i={1} time="Jun 02" text="We should go with Okta for SSO across all internal tools." />
            <Msg name="Sam Okafor" i={3} time="Jun 03" text="Counter-proposal: we'll use Auth0 — cheaper at our seat count." />
            <div style={{ opacity: note.o }}>
              <Msg name="Settled" i={2} app time="Jun 03" text={<span>🟠 <b style={{ color: "#E8912D" }}>Contested</b> — two proposals on SSO, none ratified. No binding decision yet.</span>} />
            </div>
          </SlackWindow>
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// --------------------------------------------------------- s08 /settled query
export const Query: React.FC = () => {
  const head = useRise(4), cmd = useRise(18), res = useRise(40);
  return (
    <Cream>
      <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", padding: "70px 90px" }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>Query — anywhere in Slack</Eyebrow>
          <Headline size={56} style={{ marginTop: 14 }}>The current decision, owner, and history.</Headline>
        </div>
        <div style={{ marginTop: 38, opacity: cmd.o }}>
          <SlackWindow channel="platform" w={1120} h={440}>
            <div style={{ padding: "12px 26px", fontFamily: "'Inter',sans-serif" }}>
              <span style={{ color: "#E8E8E8", fontFamily: "'Roboto Mono',monospace", fontSize: 21, background: "#33373B", padding: "3px 10px", borderRadius: 6 }}>/settled datastore</span>
            </div>
            <div style={{ opacity: res.o, padding: "4px 26px", color: "#E8E8E8", fontFamily: "'Inter',sans-serif", fontSize: 21, lineHeight: 1.5 }}>
              <div style={{ fontWeight: 800, marginBottom: 6 }}>🟢 Settled — Move primary datastore to Aurora</div>
              <Quote>Decision: we'll use Aurora as the primary datastore — managed Postgres.</Quote>
              <div style={{ color: "#9AA0A6", fontSize: 17, marginTop: 4 }}>by Dana Whitfield · May 23 · <span style={{ textDecoration: "underline" }}>permalink</span></div>
              <div style={{ color: "#9AA0A6", fontSize: 17, marginTop: 8 }}>⚪ superseded: Postgres (Apr 13), MongoDB (Apr 28)</div>
            </div>
          </SlackWindow>
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// --------------------------------------------------------- s09 App Home
export const AppHome: React.FC = () => {
  const head = useRise(4), card = useRise(16);
  const counts = [
    { n: 6, label: "settled", c: T.green },
    { n: 3, label: "contested", c: "#C0682A" },
    { n: 2, label: "awaiting", c: T.amber },
    { n: 4, label: "superseded", c: T.faint },
  ];
  const recent = [
    { dot: "🟢", t: "Standardize CI on GitHub Actions", s: "settled" },
    { dot: "🟠", t: "SSO provider — Okta vs Auth0", s: "contested" },
    { dot: "🟢", t: "Move datastore to Aurora", s: "settled" },
    { dot: "🟡", t: "Async standups in #ops", s: "awaiting ✅" },
  ];
  return (
    <Cream>
      <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", padding: "60px 90px" }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>App Home</Eyebrow>
          <Headline size={56} style={{ marginTop: 14 }}>Your whole ledger, at a glance.</Headline>
        </div>
        <div style={{ marginTop: 36, opacity: card.o, transform: `translateY(${card.y}px)`,
          width: 1180, background: "#1A1D21", borderRadius: 18, border: "1px solid #33373B",
          boxShadow: "0 40px 90px rgba(26,25,22,0.25)", padding: 38, fontFamily: "'Inter',sans-serif" }}>
          <div style={{ color: "#E8E8E8", fontSize: 26, fontWeight: 800, marginBottom: 24 }}>📒 Settled — decision ledger</div>
          <div style={{ display: "flex", gap: 56, marginBottom: 30 }}>
            {counts.map((c) => {
              const a = useRise(26 + counts.indexOf(c) * 8);
              return (
                <div key={c.label} style={{ opacity: a.o }}>
                  <div style={{ fontFamily: T.serif, fontSize: 64, fontWeight: 600, color: c.c }}>{c.n}</div>
                  <div style={{ color: "#9AA0A6", fontSize: 19 }}>{c.label}</div>
                </div>
              );
            })}
          </div>
          <div style={{ color: "#9AA0A6", fontSize: 17, fontWeight: 700, letterSpacing: 1, marginBottom: 12 }}>RECENT</div>
          {recent.map((r, k) => (
            <div key={k} style={{ opacity: useRise(46 + k * 6).o, color: "#E8E8E8", fontSize: 21, padding: "7px 0", borderTop: "1px solid #2A2E33", display: "flex", gap: 12 }}>
              <span>{r.dot}</span><span style={{ flex: 1 }}>{r.t}</span>
              <span style={{ color: "#9AA0A6", fontSize: 17 }}>{r.s}</span>
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// ============================ REAL FOOTAGE scenes ============================
// Live native-Slack recordings. Footage is the hero; opens ZOOMED on the focal
// action (so the eye lands immediately), then eases back to reveal context.
const RealClip: React.FC<{
  src: string; eyebrow: string; headline: React.ReactNode;
  startFrom?: number; focal?: [number, number]; zoom?: [number, number];
}> = ({ src, eyebrow, headline, startFrom = 0, focal = [0.5, 0.45], zoom = [1.7, 1.28] }) => {
  const f = useCurrentFrame();
  const head = useRise(2);
  const frameIn = useRise(14);
  // focal zoom: start tight on the action, ease back to reveal the interface
  const z = interpolate(f, [0, 130], [zoom[0], zoom[1]], { extrapolateRight: "clamp" });
  const VW = 1640, VH = Math.round(VW / 1.866);
  return (
    <Cream>
      <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", padding: "38px 60px" }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>{eyebrow}</Eyebrow>
          <Headline size={46} style={{ marginTop: 10 }}>{headline}</Headline>
        </div>
        {/* product window — hero */}
        <div style={{ position: "relative", marginTop: 26, opacity: frameIn.o,
          transform: `translateY(${frameIn.y}px)` }}>
          <div style={{
            width: VW, height: VH, borderRadius: 16, overflow: "hidden", position: "relative",
            border: `1px solid ${T.line}`,
            boxShadow: "0 50px 110px rgba(26,25,22,0.32), 0 12px 30px rgba(26,25,22,0.14)",
          }}>
            <OffthreadVideo src={staticFile(src)} startFrom={startFrom} muted loop
              style={{ width: "100%", display: "block",
                transformOrigin: `${focal[0] * 100}% ${focal[1] * 100}%`,
                transform: `scale(${z})` }} />
          </div>
          {/* soft reflection / floor glow for depth */}
          <div style={{ position: "absolute", left: "8%", right: "8%", bottom: -34, height: 60,
            background: "radial-gradient(60% 100% at 50% 0%, rgba(26,25,22,0.12), transparent 70%)",
            filter: "blur(6px)" }} />
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// Dynamic-camera footage scene: cursor-following spring zoom/pan (Screen-Studio style).
const RealCam: React.FC<{ src: string; startFrom?: number; track: Cam[]; eyebrow: string; headline: React.ReactNode }> =
({ src, startFrom = 0, track, eyebrow, headline }) => {
  const head = useRise(2), frameIn = useRise(12);
  return (
    <Cream>
      <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", padding: "40px 60px" }}>
        <div style={{ textAlign: "center", opacity: head.o, transform: `translateY(${head.y}px)` }}>
          <Eyebrow>{eyebrow}</Eyebrow>
          <Headline size={46} style={{ marginTop: 10 }}>{headline}</Headline>
        </div>
        <div style={{ marginTop: 26, opacity: frameIn.o, transform: `translateY(${frameIn.y}px)`, position: "relative" }}>
          <CameraRig src={src} startFrom={startFrom} track={track} />
          <div style={{ position: "absolute", left: "8%", right: "8%", bottom: -32, height: 60,
            background: "radial-gradient(60% 100% at 50% 0%, rgba(26,25,22,0.12), transparent 70%)", filter: "blur(6px)" }} />
        </div>
      </AbsoluteFill>
    </Cream>
  );
};

// Camera tracks (focal x,y normalized of footage; z zoom). Tuned per clip's content.
const T_CAPTURE: Cam[] = [
  { t: 0, x: 0.55, y: 0.4, z: 1.05 }, { t: 1.0, x: 0.82, y: 0.3, z: 1.9 },
  { t: 3.0, x: 0.82, y: 0.47, z: 2.0, click: true }, { t: 5.0, x: 0.82, y: 0.4, z: 1.85 },
];
// static Chat-tab clip: push onto the question + grounded answer (quote + source) in the lower frame
const T_ASSISTANT: Cam[] = [
  { t: 0, x: 0.45, y: 0.6, z: 1.2 }, { t: 1.8, x: 0.4, y: 0.74, z: 1.68 }, { t: 5.0, x: 0.4, y: 0.76, z: 1.7 },
];
// reuses the clean contested clip, framed on the upper "Decisions: datastore" result (Postgres→MongoDB→Aurora)
const T_QUERY: Cam[] = [
  { t: 0, x: 0.45, y: 0.4, z: 1.68 }, { t: 1.3, x: 0.43, y: 0.404, z: 2.0 }, { t: 3.6, x: 0.43, y: 0.404, z: 2.02 },
];
// static App-Home dashboard: frame the content panel (sidebar cropped out), gentle push into the list
const T_APPHOME: Cam[] = [
  { t: 0, x: 0.56, y: 0.31, z: 1.68 }, { t: 1.6, x: 0.56, y: 0.34, z: 1.8 }, { t: 4.0, x: 0.55, y: 0.4, z: 1.85 },
];
// stays on the upper decision messages — capped at y0.4/z1.5 so the Slackbot GIF (bottom) never enters
const T_PROBLEM: Cam[] = [
  { t: 0, x: 0.52, y: 0.26, z: 1.46 }, { t: 2.6, x: 0.52, y: 0.34, z: 1.5 }, { t: 5.0, x: 0.52, y: 0.4, z: 1.52 },
];
// static clip: push onto the "Decisions: sso" block (Contested Okta/Auth0) in the lower frame
const T_CONTESTED: Cam[] = [
  { t: 0, x: 0.45, y: 0.62, z: 1.25 }, { t: 1.6, x: 0.43, y: 0.78, z: 1.72 }, { t: 4.5, x: 0.43, y: 0.8, z: 1.74 },
];

export const CaptureReal: React.FC = () => (
  <RealCam src="footage/ratify.mp4" startFrom={20} track={T_CAPTURE}
    eyebrow="Capture + ratify" headline={<>It catches the decision — a human <A>confirms</A>.</>} />
);
export const AssistantReal: React.FC = () => (
  <RealCam src="footage/assistant.mp4" startFrom={12} track={T_ASSISTANT}
    eyebrow="Ask the agent" headline={<>Ask in plain language — <A>grounded</A> in the ledger.</>} />
);
export const QueryReal: React.FC = () => (
  <RealCam src="footage/contested.mp4" startFrom={12} track={T_QUERY}
    eyebrow="/settled" headline={<>The current decision, and its full <A>history</A>.</>} />
);
export const AppHomeReal: React.FC = () => (
  <RealCam src="footage/apphome.mp4" startFrom={12} track={T_APPHOME}
    eyebrow="App Home" headline={<>Your whole ledger, <A>at a glance</A>.</>} />
);
export const ProblemReal: React.FC = () => (
  <RealCam src="footage/channel.mp4" startFrom={30} track={T_PROBLEM}
    eyebrow="The problem" headline={<>Decisions get made, then <A>scroll away</A>.</>} />
);
export const ContestedReal: React.FC = () => (
  <RealCam src="footage/contested.mp4" startFrom={12} track={T_CONTESTED}
    eyebrow="When it isn't decided" headline={<>Settled says <A>contested</A>. Nothing binds yet.</>} />
);

export const SCENE_MAP: Record<string, React.FC> = {
  s01_hook: Hook, s02_problem: ProblemReal, s03_split: Split,
  s04_capture: CaptureReal, s05_ratify: Ratify, s06_contested: ContestedReal,
  s07_lifecycle: Lifecycle, s08_assistant: AssistantReal, s09_query: QueryReal,
  s10_apphome: AppHomeReal, s11_difference: Difference, s12_mcp: Mcp, s13_close: Close,
};
