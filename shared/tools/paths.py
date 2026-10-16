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
