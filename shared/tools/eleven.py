"""ElevenLabs music and sound effects, cached by request hash (key: ELEVENLABS_API_KEY in .env).

  .venv/bin/python shared/tools/eleven.py sfx "deep electrical crack" 2.5 out.mp3
  from eleven import music, sfx

Music: POST /v1/music (instrumental, prompt or composition plan). SFX: POST /v1/sound-generation.
Outputs land in audio/eleven/<kind>/<hash>.mp3 and are reused when the same request comes again.
"""
import hashlib
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from paths import AUDIO, REPO  # noqa: E402

API = "https://api.elevenlabs.io/v1"


def _key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if k:
        return k
    for line in open(os.path.join(REPO, ".env"), encoding="utf-8"):
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("ELEVENLABS_API_KEY missing")


def _post(path, body, out, fmt="mp3_44100_192"):
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return out
    req = urllib.request.Request(f"{API}{path}?output_format={fmt}", data=json.dumps(body).encode(),
                                 headers={"xi-api-key": _key(), "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=600) as r:
        data = r.read()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "wb").write(data)
    return out


def _path(kind, body):
    h = hashlib.sha1(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return os.path.join(AUDIO, "eleven", kind, f"{h}.mp3")


def music(plan=None, prompt=None, ms=None, seed=None, take=0):
    """Instrumental cue. plan: music_v1 composition plan (sections); or a prompt + length."""
    if plan is not None:
        body = {"composition_plan": plan, "model_id": "music_v1"}
        if seed is not None:
            body["seed"] = seed
    else:
        body = {"prompt": prompt, "music_length_ms": ms, "force_instrumental": True, "model_id": "music_v1"}
    out = _path("music", {**body, "take": take})
    return _post("/music", body, out)


def sfx(text, seconds=None, influence=0.45, take=0):
    body = {"text": text, "model_id": "eleven_text_to_sound_v2", "prompt_influence": influence}
    if seconds:
        body["duration_seconds"] = seconds
    out = _path("sfx", {**body, "take": take})
    return _post("/sound-generation", body, out)


if __name__ == "__main__":
    if sys.argv[1] == "sfx":
        print(sfx(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else None))
