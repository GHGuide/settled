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
