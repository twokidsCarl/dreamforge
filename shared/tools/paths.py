"""Where things live. Every tool resolves the current episode through here.

  repo/
    shared/tools      this toolchain (all episodes)
    shared/blender    shared Blender modules: scene setup, materials, visual-language styles
    episodes/<EPISODE>/  research, script, storyboard, subs, blender/{scripts,shots}, mograph,
                         audio/ and renders/ (both git-ignored)

The episode defaults to DEFAULT_EPISODE; override with DREAMFORGE_EPISODE=E2-xxx (or a tool's
--episode flag where offered). DREAMFORGE_RENDER_DIR overrides the render root (e.g. an external
drive).
"""
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SHARED = os.path.join(REPO, "shared")
DEFAULT_EPISODE = "E1-euv-lithography"


def episode():
    return os.environ.get("DREAMFORGE_EPISODE", DEFAULT_EPISODE)


def set_episode(name):
    if name:
        os.environ["DREAMFORGE_EPISODE"] = name
    global EPISODE, EP, AUDIO, RENDERS
    EPISODE = episode()
    EP = os.path.join(REPO, "episodes", EPISODE)
    AUDIO = os.path.join(EP, "audio")
    RENDERS = os.environ.get("DREAMFORGE_RENDER_DIR", os.path.join(EP, "renders"))


EPISODE = EP = AUDIO = RENDERS = None
set_episode(None)


def timed_shots(segments=None, quiet=False):
    """storyboard.timed.yaml 的镜头列表；配音定时前还没有这个文件，就回退到 storyboard.yaml
    的 duration（按顺序累加出 start），并打印一行警告。segments: 只取这些段（如 ["A0"]）。"""
    import sys
    import yaml
    timed = os.path.join(EP, "storyboard", "storyboard.timed.yaml")
    if os.path.exists(timed):
        shots = yaml.safe_load(open(timed, encoding="utf-8"))["shots"]
    else:
        if not quiet:
            print(f"[paths] 警告：{timed} 不存在，回退到 storyboard.yaml 的 duration（配音定时后会改变）",
                  file=sys.stderr, flush=True)
        shots = yaml.safe_load(open(os.path.join(EP, "storyboard", "storyboard.yaml"), encoding="utf-8"))["shots"]
        t = 0.0
        for s in shots:
            s["start"] = round(t, 3)
            t += s["duration"]
    return [s for s in shots if not segments or s["segment"] in segments]
