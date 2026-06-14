#!/usr/bin/env python3
"""gen-vo — generate one voiceover mp3 per scene + measure durations.

Engine-pluggable (reads video.config.json voice.engine):
  - elevenlabs : final quality, commercial license (uses ELEVENLABS_API_KEY)
  - edge-tts   : free, for iteration passes (--engine edge-tts to force)

Portable: works for any project that follows video/STRUCTURE.md. Reads:
  video/video.config.json, video/script/script.json
Writes:
  video/vo/<scene_id>.mp3, video/vo/vo.manifest.json

Usage:
  python video/pipeline/gen_vo.py                 # engine from config
  python video/pipeline/gen_vo.py --engine edge-tts   # force free iteration
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

VIDEO = Path(__file__).resolve().parent.parent
ROOT = VIDEO.parent


def load_env():
    """Read KEY=VALUE from the project .env so we don't depend on shell export."""
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def ffprobe_dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return round(float(out.stdout.strip()), 3)
    except ValueError:
        return 0.0


def gen_elevenlabs(text: str, out: Path, voice: dict) -> None:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY missing")
    vid = voice["id"]
    body = json.dumps({
        "text": text,
        "model_id": voice.get("model", "eleven_multilingual_v2"),
        "voice_settings": voice.get("settings", {"stability": 0.45, "similarity_boost": 0.8}),
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r, open(out, "wb") as f:
        f.write(r.read())


def gen_edge(text: str, out: Path, voice: dict) -> None:
    import asyncio

    import edge_tts

    vid = voice.get("id", "en-US-AndrewNeural")
    rate = voice.get("rate", "+0%")

    async def _run():
        await edge_tts.Communicate(text, vid, rate=rate).save(str(out))

    asyncio.run(_run())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["elevenlabs", "edge-tts"], default=None)
    args = ap.parse_args()
    load_env()

    cfg = json.loads((VIDEO / "video.config.json").read_text())
    scenes = json.loads((VIDEO / "script" / "script.json").read_text())["scenes"]
    voice = cfg["voice"]
    engine = args.engine or voice.get("engine", "edge-tts")
    if engine == "edge-tts":
        voice = voice.get("fallback", {"engine": "edge-tts", "id": "en-US-AndrewNeural"})

    vo_dir = VIDEO / "vo"
    vo_dir.mkdir(exist_ok=True)
    manifest = {"engine": engine, "voice": voice.get("id"), "scenes": []}
    total = 0.0
    for s in scenes:
        out = vo_dir / f"{s['id']}.mp3"
        if engine == "elevenlabs":
            gen_elevenlabs(s["vo"], out, voice)
        else:
            gen_edge(s["vo"], out, voice)
        dur = ffprobe_dur(out)
        total += dur
        manifest["scenes"].append({"id": s["id"], "mp3": out.name, "duration": dur})
        print(f"  {s['id']:14} {dur:6.2f}s  ({engine})")

    manifest["total_duration"] = round(total, 2)
    (vo_dir / "vo.manifest.json").write_text(json.dumps(manifest, indent=2))
    cap = cfg.get("max_duration_sec", 180)
    print(f"\nTotal VO: {total:.1f}s  (cap {cap}s)  -> {'OK' if total < cap else 'OVER CAP'}")
    if total >= cap:
        print("WARNING: VO alone exceeds cap. Tighten script before adding pauses.", file=sys.stderr)


if __name__ == "__main__":
    main()
