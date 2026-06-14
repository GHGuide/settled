import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig, useCurrentFrame, interpolate } from "remotion";
import { SCENE_MAP } from "./scenes/Scenes";
import vo from "./data/vo.manifest.json";
import { T } from "./theme";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadFraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as loadMono } from "@remotion/google-fonts/RobotoMono";

loadInter();
loadFraunces();
loadMono();

// Per-scene hold AFTER the VO line — lets the visual breathe (calm pacing). Tightened.
const HOLD: Record<string, number> = {
  s01_hook: 1.5, s02_problem: 1.8, s03_split: 4.0, s04_capture: 1.0, s05_ratify: 1.2,
  s06_contested: 2.0, s07_lifecycle: 2.2, s08_assistant: 1.0, s09_query: 1.0,
  s10_apphome: 1.0, s11_difference: 2.5, s12_mcp: 2.2, s13_close: 2.8,
};
const DEFAULT_HOLD = 1.6;

// Real-footage scenes: the scene must last at least the playable clip length so the
// live recording plays through. Values = clip seconds AFTER startFrom.
const CLIP_LEN: Record<string, number> = {
  s02_problem: 7.0, s04_capture: 5.5, s06_contested: 6.0, s08_assistant: 8.0,
  s09_query: 5.3, s10_apphome: 4.3,
};

export const sceneFrames = (fps: number) =>
  vo.scenes.map((s) => {
    const voPlusHold = s.duration + (HOLD[s.id] ?? DEFAULT_HOLD);
    const clip = CLIP_LEN[s.id] ?? 0;
    return { id: s.id, frames: Math.round(Math.max(voPlusHold, clip) * fps) };
  });

export const totalFrames = (fps: number) =>
  sceneFrames(fps).reduce((a, s) => a + s.frames, 0);

// Scale-push cross-dissolve: scene eases in (slight up-scale) + out, through the cream bg.
const FADE = 14;
const FadeScene: React.FC<{ frames: number; children: React.ReactNode }> = ({ frames, children }) => {
  const f = useCurrentFrame();
  const opacity = interpolate(f, [0, FADE, frames - FADE, frames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const scale = interpolate(f, [0, FADE, frames - FADE, frames], [1.012, 1, 1, 0.994], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ opacity, transform: `scale(${scale})` }}>{children}</AbsoluteFill>;
};

export const SettledVideo: React.FC = () => {
  const { fps } = useVideoConfig();
  const segs = sceneFrames(fps);
  // scene start frames for the music envelope
  const starts: Record<string, [number, number]> = {};
  let acc = 0;
  for (const s of segs) { starts[s.id] = [acc, acc + s.frames]; acc += s.frames; }
  const total = acc;

  // music: gentle bed, ducked under dense VO, swelled at the split reveal + the close.
  const volumeAt = (f: number) => {
    let v = 0.12;
    const swell = (range?: [number, number], peak = 0.2) => {
      if (!range) return;
      const [a, b] = range;
      const e = interpolate(f, [a, a + 25, b - 25, b], [v, peak, peak, v],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
      if (f >= a && f <= b) v = e;
    };
    swell(starts["s03_split"], 0.19);
    swell(starts["s11_difference"], 0.18);
    swell(starts["s13_close"], 0.2);
    const fadeIn = interpolate(f, [0, fps * 1.5], [0, 1], { extrapolateRight: "clamp" });
    const fadeOut = interpolate(f, [total - fps * 4, total], [1, 0], { extrapolateLeft: "clamp" });
    return v * fadeIn * fadeOut;
  };

  let from = 0;
  return (
    <AbsoluteFill style={{ background: T.bg }}>
      {/* CC0 ambient bed (OpenGameArt — "First Light Particles", CC0 1.0, no attribution) */}
      <Audio src={staticFile("audio/ambient.mp3")} volume={(f) => volumeAt(f)} />
      {segs.map((seg) => {
        const Comp = SCENE_MAP[seg.id];
        const seq = (
          <Sequence key={seg.id} from={from} durationInFrames={seg.frames} name={seg.id}>
            <FadeScene frames={seg.frames}>{Comp ? <Comp /> : null}</FadeScene>
            <Audio src={staticFile(`vo/${seg.id}.mp3`)} />
          </Sequence>
        );
        from += seg.frames;
        return seq;
      })}
    </AbsoluteFill>
  );
};
