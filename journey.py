"""Render the same interactive journey used by the standalone public site."""
import base64
import json
from pathlib import Path
import re

ROOT = Path(__file__).parent


def image_uri(name):
    image = (ROOT / "assets" / name).read_bytes()
    return "data:image/webp;base64," + base64.b64encode(image).decode("ascii")


def render(story, selected="nian-jinmen"):
    template = (ROOT / "journey.html").read_text(encoding="utf-8")
    styles = (ROOT / "journey.css").read_text(encoding="utf-8")
    script = (ROOT / "journey.js").read_text(encoding="utf-8")
    records = re.search(r'(<script id="records" type="application/json">)(.*?)(</script>)', template)
    summaries = {record["id"]: record["short"] for record in json.loads(records[2])}
    cases = [*story["cases"], *(case for group in story["extensions"] for case in group["cases"])]
    for case in cases:
        summaries.setdefault(case["id"], case["title"])
    images = {case["id"]: image_uri(case["id"] + ".webp") for case in cases}
    data = json.dumps([dict(case, short=summaries[case["id"]]) for case in cases], ensure_ascii=False)
    template = template[:records.start(2)] + data.replace("<", r"\u003c") + template[records.end(2):]
    for case_id, uri in images.items():
        template = template.replace(f'src="{case_id}.webp"', f'src="{uri}"')
    for name in ("coast.webp", "lantern.webp", "nian-quanzhou.webp"):
        styles = styles.replace(f"url({name})", f'url("{image_uri(name)}")')
    config = json.dumps({"selected": selected})
    return (template.replace('<link rel="stylesheet" href="style.css">', f"<style>{styles}</style>")
            .replace('<script defer src="app.js"></script>', "")
            .replace("</body>", f"<script>const embedded = {config};\n{script}</script></body>"))


