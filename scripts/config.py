"""Tiny config loader shared by every script. Order: environment (EXPLAINER_<KEY>) > <skill>/config.local.json (git-ignored, per user) > built-in default.
Keys: handle (header text, e.g. "@yourhandle") · music_dir · sfx_dir · drive_dest (rclone path) · kit_lint (path to an extra posting-kit linter) · personal (path to a rules file the agent must read)."""
import json, os
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_c = None
def get(key, default=None):
    global _c
    if os.environ.get("EXPLAINER_" + key.upper()): return os.environ["EXPLAINER_" + key.upper()]
    if _c is None:
        try: _c = json.load(open(os.path.join(SKILL, "config.local.json")))
        except Exception: _c = {}
    v = _c.get(key, default); return os.path.expanduser(v) if isinstance(v, str) and v.startswith("~") else v
