import React from "react";
import { OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { CameraMotionBlur } from "@remotion/motion-blur";
import { T } from "./theme";

// A camera keyframe: time (sec into the SCENE), focal point (0..1 of footage), zoom, optional click.
export type Cam = { t: number; x: number; y: number; z: number; click?: boolean };

const FOOT_W = 1920;
const FOOT_H = 1120; // cropped clips are 1920x1120 (crop 3600:2100 -> scale 1920)

// spring-eased value through keyframes (momentum + slight overshoot)
function camAt(track: Cam[], tSec: number, fps: number) {
  if (track.length === 1) return track[0];
  let i = 0;
  while (i < track.length - 1 && tSec >= track[i + 1].t) i++;
  const a = track[i], b = track[Math.min(i + 1, track.length - 1)];
  if (a === b) return a;
  const segFrames = Math.max(1, (b.t - a.t) * fps);
  const p = spring({ frame: (tSec - a.t) * fps, fps, durationInFrames: segFrames,
    config: { damping: 18, mass: 0.95, stiffness: 90 } });
  return {
    x: a.x + (b.x - a.x) * p, y: a.y + (b.y - a.y) * p, z: a.z + (b.z - a.z) * p,
    // cursor leads the camera a touch
    cp: Math.min(1, p * 1.5), cx: a.x + (b.x - a.x) * Math.min(1, p * 1.5),
    cy: a.y + (b.y - a.y) * Math.min(1, p * 1.5), click: b.click,
  } as any;
}

const Cursor: React.FC<{ x: number; y: number; pulse: number }> = ({ x, y, pulse }) => (
  <div style={{ position: "absolute", left: x, top: y, transform: "translate(-3px,-2px)", pointerEvents: "none" }}>
    {pulse > 0 && (
      <div style={{ position: "absolute", left: 0, top: 0, width: 60, height: 60,
        marginLeft: -28, marginTop: -26, borderRadius: 999,
        border: `3px solid ${T.clay}`, opacity: (1 - pulse) * 0.7, transform: `scale(${0.3 + pulse * 1.4})` }} />
    )}
    <svg width="30" height="38" viewBox="0 0 24 30" style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.4))" }}>
      <path d="M2 2 L2 22 L7 17 L11 27 L14 26 L10 16 L17 16 Z" fill="#fff" stroke="#1a1916" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  </div>
);

export const CameraRig: React.FC<{ src: string; startFrom?: number; track: Cam[]; vw?: number }> =
({ src, startFrom = 0, track, vw = 1560 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tSec = f / fps;
  const vh = Math.round(vw * 9 / 16);
  const c: any = camAt(track, tSec, fps);

  const fh = vw * (FOOT_H / FOOT_W);             // footage height at width = vw
  const tx = vw / 2 - c.x * vw * c.z;
  const ty = vh / 2 - c.y * fh * c.z;
  // cursor screen position (through current camera)
  const curX = tx + c.cx * vw * c.z;
  const curY = ty + c.cy * fh * c.z;
  // click pulse window around a click keyframe
  let pulse = 0;
  for (const k of track) {
    if (k.click) {
      const d = tSec - k.t;
      if (d >= 0 && d < 0.6) pulse = Math.max(pulse, 1 - d / 0.6);
    }
  }

  return (
    <div style={{ width: vw, height: vh, borderRadius: 16, overflow: "hidden", position: "relative",
      border: `1px solid ${T.line}`,
      boxShadow: "0 50px 110px rgba(26,25,22,0.32), 0 12px 30px rgba(26,25,22,0.14)" }}>
      <CameraMotionBlur shutterAngle={150} samples={6}>
        <div style={{ position: "absolute", left: 0, top: 0, width: vw, height: fh,
          transformOrigin: "0 0", transform: `translate(${tx}px, ${ty}px) scale(${c.z})` }}>
          <OffthreadVideo src={staticFile(src)} startFrom={startFrom} muted loop
            style={{ width: vw, height: fh, display: "block" }} />
        </div>
      </CameraMotionBlur>
      <Cursor x={curX} y={curY} pulse={pulse} />
    </div>
  );
};
