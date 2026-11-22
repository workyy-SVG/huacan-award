import base64
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent


def art(name):
    raw = (ROOT / "assets" / (name + ".webp")).read_bytes()
    return "data:image/webp;base64," + base64.b64encode(raw).decode()


def card(case):
    c = {key: escape(value) for key, value in case.items() if isinstance(value, str)}
    title = c.get("meal_name", c["title"])
    return f"""<article class="card" id="{c['id']}"><img src="{art(c['id'])}" alt="">
    <div class="copy"><h3><strong>{c['place']}</strong>｜{title}</h3><p>{c['recorded_action']}</p>
    <details><summary>阅读记录</summary><p>{c['body']}</p>{c.get('source_quote', '')}</details>
    <a href="{c['source_url']}" target="_blank" rel="noopener">{c['source_title']} ↗</a></div></article>"""


def render(story, selected="nian-jinmen"):
    primary = story["cases"]
    extended = [c for section in story["extensions"] for c in section["cases"]]
    cases = primary + extended
    options = []
    for c in cases:
        attrs = " ".join(f'data-{attr}="{escape(c[key])}"' for attr, key in
                         [('detail', 'recorded_action'), ('source', 'source_title'), ('url', 'source_url')])
        active = " selected" if c["id"] == selected else ""
        options.append(f"<option {attrs}{active}>{escape(c['place'])} · {escape(c['title'])}</option>")
    html = (ROOT / "journey.html").read_text(encoding="utf-8")
    html = html.replace("<main>", f"<body style=\"--land:url('{art('coast')}')\"><main>")
    route = "".join(f'<a href="#{escape(c["id"])}">{escape(c["place"])}</a>' for c in cases)
    return (html.replace("__ROUTE__", route).replace("__PAIR__", "".join(map(card, primary)))
            .replace("__MORE__", "".join(map(card, extended))).replace("__OPTIONS__", "".join(options))
            .replace("__DISCOVERY__", escape(story["discovery"])))
