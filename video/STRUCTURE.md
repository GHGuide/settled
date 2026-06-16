# Automated Video Pipeline — portable convention

Project-agnostic. Any project that wants an auto-edited demo video adopts this exact
`video/` subtree. A video-editor agent reads ONLY `video.config.json` + `script/script.json`
to know everything project-specific; all logic/tools are identical across projects.

Goal aesthetic: "Claude Code YouTube" — auto-zoom screen capture, code-driven motion
graphics, clean neural VO. Fully agent-driveable. Fully free. macOS.

## Folder layout (per project)
```
<project>/video/
  video.config.json          # ONLY per-project file an agent must read first
  STRUCTURE.md               # this file (so a cold agent self-onboards)
  script/
    script.md                # human-readable narration + scene beats (source of truth for edits)
    script.json              # machine: ordered scenes (generated/synced from script.md)
  capture/
    raw/                     # raw screen recordings (ffmpeg / Screen Studio) — gitignored
    capture.manifest.json    # clip file -> scene_id, trim in/out, zoom keyframes
  vo/
    <scene_id>.mp3           # one TTS file per scene (generated) — gitignored
    vo.manifest.json         # scene_id -> mp3 path, measured duration (sec)
  assets/                    # logos, architecture.png, lower-thirds, bg music (licensed/none)
  remotion/                  # Remotion project: package.json, src/Root.tsx, src/scenes/, src/components/
  out/                       # final renders — gitignored
    <project>-demo.mp4       # master (1080p)
    <project>-demo-yt.mp4    # YouTube upload (<3:00, H.264)
    thumbnail.png
```

## scene contract (script.json)
```json
{
  "project": "settled",
  "scenes": [
    {
      "id": "s01_hook",
      "vo": "Every team loses decisions to scrollback...",
      "target_sec": 12,
      "capture": null,                 // null = motion-graphic-only scene
      "captions": true,
      "graphic": "title_card"          // component name in remotion/src/components
    },
    {
      "id": "s04_ratify",
      "vo": "One check mark settles it.",
      "target_sec": 8,
      "capture": "capture/raw/ratify.mov",
      "trim": [2.0, 9.5],              // seconds in/out of raw clip
      "zoom": [{ "t": 0.5, "rect": [620,300,360,200], "scale": 1.8 }],
      "captions": true
    }
  ]
}
```
Rules an agent follows:
- VO is the timing backbone. Actual scene length = measured VO duration (vo.manifest) + 0.6s pad,
  NOT `target_sec` (that's only the writing budget).
- `capture: null` → render a motion graphic for that scene (no recording needed).
- A scene with `capture` but no matching file in `capture/raw/` → BLOCKED; agent logs the
  missing clip in `capture.manifest.json.todo[]` and renders a placeholder card, never silently drops it.
- Total final duration MUST be < the `max_duration_sec` in video.config.json. Agent fails the
  build (non-zero exit) if exceeded — never ships an over-length video.

## deterministic pipeline (orchestrator runs in order)
1. **sync-script**   — regenerate `script.json` from `script.md` (parse beats).
2. **gen-vo**        — for each scene, TTS `vo` text → `vo/<id>.mp3`; measure duration → `vo.manifest.json`.
3. **capture-gate**  — verify every `capture` ref exists in `capture/raw/`. Missing → list + stop (human/agent records them).
4. **build**         — `npx remotion render` composes scenes: capture clip → trim → zoom keyframes → over-VO → captions → graphics.
5. **validate**      — assert: duration < max, resolution == target, audio track present, no placeholder cards in final.
6. **package**       — write `out/*-yt.mp4` (H.264, faststart) + thumbnail.

Each step idempotent + resumable. Re-running with unchanged inputs is a no-op.

## toolchain (all free, all CLI/agent-driveable)
| Step | Tool | Notes |
|---|---|---|
| capture | `ffmpeg -f avfoundation` OR Screen Studio (manual, higher polish) | agent drives demo via browser MCP while ffmpeg records |
| zoom/motion/captions | **Remotion** (React, free for individuals) | scenes as code; auto-zoom = animated transform on capture |
| VO | **edge-tts** (pip, MS neural, $0) default · Kokoro (local, higher quality) opt-in | voice id set in config |
| render | `npx remotion render` | H.264 mp4 |
| diagram | architecture.png from project's `architecture.md` (mermaid-cli) | dropped in assets/ |

## orchestrator integration
- Orchestrator holds ONE canonical copy of this `video/` template (minus project files).
- Per project: `cp -r template/video <project>/ && edit video.config.json`.
- Orchestrator's video job = run the 6 pipeline steps against `<project>/video/`.
- The editor agent needs NOTHING about a project except its `video.config.json` + `script/`.
  Everything else (tools, step logic, Remotion components) is shared + identical.
- ISOLATION: each project's captures/vo/out stay inside that project's folder. The template
  is shared; the artifacts never cross project boundaries.
```

## LESSONS LEARNED (v1 → v14) — bake these in, each prevents a real failure

**Aesthetic (locked):** warm cream bg `#F2EFE7`, clay accent `#C9603A`, serif Fraunces (headlines),
Inter (body), Roboto Mono (code). Female "Claude-presentation" VO — ElevenLabs **Sarah**
(`EXAVITQu4vr4xnSDxMaL`, `eleven_multilingual_v2`). Reject: dark generic-keynote look, male/generic AI voice.

**Lead with the differentiator.** The cold-open's first ~15s must show the ONE thing that's unique
(here: an agent caught by the guardrail, rewriting its own code), not a generic problem statement.

**Capture is the failure-prone step. Run it on a pristine stage:**
- **Freeze the demo data state FIRST** (final seed) so every clip matches — else counts/contents drift between scenes.
- **Quit Magnet** (blocks computer-use clicks) and **Wispr Flow** (`pkill -9 -f "Wispr Flow"` — its floating overlay blocks dialog clicks).
- `open_application` the target app → it returns to fullscreen on screen 0. Single display.
- **Record STATIC** (no scrolling during capture) — scrolling footage drifts the virtual camera into clutter.
- **Move the cursor to the sidebar before recording** (kills hover toolbars).
- Scroll clutter off-screen first (Slack's "invites sent" GIF, "50% off Pro" promo).
- **GATE — verify ONE raw frame (`ffmpeg -ss N -i raw.mov -frames:v 1 chk.png`) BEFORE cropping.**
  This is the check that catches another window stealing screen-0 foreground / tiling beside the app
  (the contamination that leaked other content). Never crop+wire a clip you haven't eyeballed.
- Crop uniformly: `crop=3600:2100:0:60,scale=1920:-2` → 1920×1120 (retina screen 0).

**Camera (Screen-Studio style):** `CameraRig.tsx` — spring-eased focal `{x,y,z}` keyframes + motion blur
+ synthetic cursor. **Compute focal x/y/z from measured content coords** to crop residual clutter
(sidebar/GIF), and **verify each clip with `remotion still --frame=N` before any full render.**

**VO timing:** scene length = `max(VO_dur + hold, clipLen)`. **Regenerate VO for CHANGED scenes only**
(cost + avoids drift). **Whenever a scene's VO duration changes, re-sync its reveal frame-delays** —
animation desyncs otherwise.

**Wire footage → scene carefully** (a past bug had `home.mp4`/`apphome.mp4` swapped). Name clips by role.

**Render:** `npx remotion render Settled out/x.mp4 --codec=h264 --crf=20 --concurrency=2`.
**Default concurrency OOMs (exit 137) — always `--concurrency=2`.**

**QA gate before shipping:** extract a mid-frame from EVERY scene → tile montage (`ffmpeg tile`) →
eyeball for clutter / content-match / VO-sync. Re-render only flagged scenes. Confirm duration < cap (3:00).

**Deliver:** upload to YouTube (allowed hosts: YouTube/Vimeo/Facebook/Youku) → link in the submission.
