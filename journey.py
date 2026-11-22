"""Render the illustrated Nian journey as a self-contained interactive page."""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).parent


def render(story, selected="nian-jinmen"):
    cases = [*story["cases"], *(case for group in story["extensions"] for case in group["cases"])]
    data = json.dumps({"cases": cases, "selected": selected}, ensure_ascii=False)
    poster = base64.b64encode((ROOT / "assets/nian-portrait.webp").read_bytes()).decode()
    return ((ROOT / "journey.html").read_text(encoding="utf-8")
            .replace("__POSTER__", poster).replace("__DATA__", data.replace("<", r"\u003c")))
