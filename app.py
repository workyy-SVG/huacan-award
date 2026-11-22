import json
import base64
from html import escape
from pathlib import Path

import streamlit as st


TITLE = "字里寻踪：两岸四海的生活印记"
FULL_TITLE = f"《{TITLE}——汉字与民俗故事交互设计》"
DATA_PATH = Path(__file__).parent / "data" / "nian-quanzhou-jinmen.json"
story = json.loads(DATA_PATH.read_text(encoding="utf-8"))

st.set_page_config(page_title=TITLE, page_icon="年")
st.markdown("""
<style>
.stApp {
  background-color:#f2f1ee;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='paper'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.77' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23paper)' opacity='.14'/%3E%3C/svg%3E"),
    radial-gradient(ellipse at 52% 18%,#fdfcf9 0%,transparent 56%),
    linear-gradient(155deg,#f4f3f0 28%,#e6e5e1 100%);
  color:#302b28;
}
.block-container { max-width:860px; padding-top:3rem; }
.seal { display:grid; place-items:center; width:88px; height:88px;
background:#a63227; color:#fff4dc; border-radius:12px;
font: bold 58px "STKaiti","KaiTi",serif; margin:0 0 24px; }
h1,h2,h3 { font-family:"Noto Serif CJK SC","Songti SC","SimSun",serif !important; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:#decab5; }
</style>
""", unsafe_allow_html=True)

all_cases = story["cases"] + [
    case for section in story["extensions"] for case in section["cases"]
]
case_ids = {case["id"] for case in all_cases}


def render_journey(story, chosen_case):
    ink_route = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 410 340" preserveAspectRatio="none">
  <defs><filter id="ink" x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence baseFrequency=".032 .11" numOctaves="3" seed="17" result="grain"/>
    <feDisplacementMap in="SourceGraphic" in2="grain" scale="11"/>
  </filter></defs>
  <path d="M56 16C145 21 260 9 273 36S232 89 242 101
           218 125 168 155 193 158 290 169 248 193 152 234 179 253
           240 289 235 309 166 334 151 340"
        fill="none" stroke="#494641" stroke-opacity=".34" stroke-width="7"
        stroke-linecap="round" filter="url(#ink)"/>
  <path d="M56 16C145 21 260 9 273 36S232 89 242 101
           218 125 168 155 193 158 290 169 248 193 152 234 179 253
           240 289 235 309 166 334 151 340"
        fill="none" stroke="#514d48" stroke-opacity=".62" stroke-width="1.6"/>
  <path d="M76 204Q74 226 102 226H152M259 153H289M58 306H80L101 329M227 282Q231 306 264 306"
        fill="none" stroke="#989087" stroke-opacity=".58" stroke-width="1"/>
  <g fill="#514d48"><circle cx="273" cy="36" r="3"/><circle cx="242" cy="101" r="3"/>
  <circle cx="289" cy="153" r="2"/><circle cx="203" cy="215" r="2"/></g>
</svg>
"""
    ink = base64.b64encode(ink_route.encode()).decode("ascii")
    st.html(f"""
<style>
.nian-page {{width:min(100%,410px); margin:0 auto; color:#332c27;
  font-family:"Songti SC","Noto Serif CJK SC","SimSun",serif;}}
.nian-identity {{display:flex; align-items:center; gap:14px; margin-bottom:21px;}}
.nian-stamp {{display:grid; place-items:center; flex:0 0 44px; height:44px;
  border-radius:7px; color:#fff4dc; background:linear-gradient(135deg,#8f211d,#aa3829);
  font:bold 29px KaiTi,serif;}}
.nian-meta,.nian-page .nian-copy {{font:11px/1.6 system-ui,sans-serif;}}
.nian-page h1 {{font-size:clamp(20px,4.7vw,24px); line-height:1.3; margin:0 0 7px; padding:0;}}
.nian-map {{position:relative; aspect-ratio:410/340; margin-top:44px;
  background:url('data:image/svg+xml;base64,{ink}') center/100% 100% no-repeat;}}
.nian-label,.nian-box {{position:absolute; text-decoration:none; color:inherit;
  background:#fffdf9ee; border:1px solid #ded5cc; border-radius:8px;
  box-shadow:0 2px 6px #40302213;}}
.nian-label {{padding:3px 8px; font-size:clamp(12px,3.4vw,17px); font-weight:bold;}}
.nian-box {{padding:6px 8px; box-sizing:border-box; font-size:clamp(9px,2.45vw,11px); line-height:1.35;}}
.nian-box strong {{display:block; font-size:1.25em; margin-bottom:3px;}}
.nian-card {{padding:9px 10px; background:#fffdf9ba; border-radius:8px; margin-bottom:6px;}}
.nian-card strong {{font-size:13px;}}
.nian-page a:hover,.nian-page a:focus-visible {{outline:2px solid #a63227;}}
</style>
<article class="nian-page">
  <div class="nian-identity"><span class="nian-stamp">年</span>
    <div class="nian-meta">读音　nián<br>字形 · 两岸 · 港澳 · 海外</div></div>
  <h1>{escape(story["cross_strait_question"])}</h1>
  <p class="nian-copy">{escape(story["intro"])}</p>
  <nav class="nian-map" aria-label="寻踪路线">
    <a class="nian-label" style="left:0;top:1%" href="#nian-form" target="_self">字形</a>
    <a class="nian-label" style="left:58%;top:17%" href="#nian-strait" target="_self">两岸</a>
    <a class="nian-box" style="left:0;top:30%;width:41%" href="#nian-strait" target="_self">
      <strong>两岸案例</strong>泉州的游子赶回家吃年饭。金门的记录里，未能返乡的人也有一副碗筷。</a>
    <a class="nian-box" style="right:0;top:33%;width:29%" href="#nian-discovery" target="_self">
      <strong>四海</strong>从留一副碗筷，到邀请朋友一起捞鱼生。</a>
    <a class="nian-label" style="left:0;top:86%" href="#nian-hkmo" target="_self">港澳</a>
    <a class="nian-label" style="left:66%;top:86%" href="#nian-overseas" target="_self">海外</a>
  </nav>
  <div class="nian-card"><strong>寻踪卡</strong>
    <div class="nian-copy">{escape(chosen_case["place"])} · {escape(chosen_case["title"])}<br>
    {escape(chosen_case["recorded_action"])}</div></div>
</article>
""")


selected = st.query_params.get("story")
lookup = st.query_params.get("hanzi", "").strip()
if lookup == story["character"] and not selected:
    selected = "nian"
if selected not in case_ids | {"nian"}:
    assets = DATA_PATH.parent
    cover = base64.b64encode((assets / "globe-cover-reference.png").read_bytes()).decode("ascii")
    st.html(f"""
<style>
.block-container {{ padding:0 !important; }}
[data-testid="stHeader"] {{ display:none; }}
.globe-cover {{
  width:min(100%, 900px, calc((100dvh - 12px) * 1600 / 2416));
  aspect-ratio:1600/2416; margin:auto;
  position:relative; container-type:inline-size; overflow:hidden;
  background:#f8f6f1;
}}
.globe-art {{
  position:absolute; top:-20cqw; left:0; display:block;
  width:100%; height:auto; pointer-events:none;
}}
.globe-start,.globe-search {{ position:absolute; border-radius:999px; }}
.globe-start {{ left:27%; top:116.53cqw; width:46.5%; height:9.97cqw; }}
.globe-search {{ left:7.7%; top:135.75cqw; width:84.8%; height:9.79cqw; }}
.globe-search input {{
  width:100%; height:100%; border:0; border-radius:inherit; box-sizing:border-box;
  background:transparent; color:transparent; padding:0 5%;
  font:clamp(16px,3.5cqw,20px) "Songti SC","SimSun",serif;
}}
.globe-search input:focus,.globe-search input:valid {{background:#f7f4ef;color:#302b28;}}
.globe-start:focus-visible,.globe-search input:focus-visible {{outline:2px solid #8d291a;}}
@media (min-width: 900px) {{
  .block-container {{ max-width:1080px; }}
}}
</style>
<main class="globe-cover" aria-label="字里寻踪。 同一个字，连接不同地方的生活记录">
  <img class="globe-art" src="data:image/png;base64,{cover}" width="1600" height="2848" alt="折页地图，标有两岸、香港、澳门与海外华人社群">
  <a class="globe-start" href="?story=nian" target="_self" aria-label="选一个字，开始寻踪"></a>
  <form class="globe-search" method="get">
    <input name="hanzi" aria-label="查一个我感兴趣的字" autocomplete="off" enterkeyhint="search" required>
  </form>
</main>
""")
    if lookup:
        st.info("当前预览已收录「年」字，请试试输入「年」。")
else:
    if st.button("返回首页"):
        st.query_params.clear()
        st.rerun()
    chosen_case = next((item for item in all_cases if item["id"] == selected), story["cases"][1])
    render_journey(story, st.session_state.get(f"journey-choice-{selected}", chosen_case))
    choice = st.radio(
        "哪一个细节你想带走？",
        options=all_cases,
        key=f"journey-choice-{selected}",
        index=all_cases.index(chosen_case),
        format_func=lambda case: f"{case['place']} · {case['title']}",
    )
    note = (
        f"字里寻踪 · 年\n{choice['place']}｜{choice['title']}\n"
        f"{choice['recorded_action']}\n出处：{choice['source_title']}\n{choice['source_url']}"
    )
    st.download_button("保存寻踪记录", note, "我的寻踪卡-年.txt", "text/plain")
    st.header("字形观察", anchor="nian-form")
    st.write("年（nián）是这里的观察起点。下面沿着这个字，看各地如何过年。")
    st.link_button("查阅「年」字字源资料", "https://humanum.arts.cuhk.edu.hk/Lexis/lexi-mf/search.php?word=%E5%B9%B4")
    if selected in case_ids:
        case = next(item for item in all_cases if item["id"] == selected)
        st.caption(f"从{case['place']}出发")
    st.header("第一站 · 两岸", anchor="nian-strait")
    st.write(story["cross_strait_question"])
    for heading, field in [
        ("这顿饭怎么称呼？", "meal_name"),
        ("记录了什么动作？", "recorded_action"),
    ]:
        st.subheader(heading)
        for case in story["cases"]:
            with st.container(border=True):
                st.markdown(f"**{case['place']}**")
                st.write(case[field])
    with st.expander("查看两地故事与原文出处"):
        for case in story["cases"]:
            st.markdown(f"**{case['place']} · {case['title']}**")
            st.write(case["body"])
            st.write(f"“{case['source_quote']}”")
            st.link_button(case["source_title"], case["source_url"])
        st.caption(story["editor_note"])
    for section, anchor in zip(story["extensions"], ("nian-hkmo", "nian-overseas")):
        st.header(section["heading"], anchor=anchor)
        st.write(section["question"])
        for case in section["cases"]:
            with st.container(border=True):
                st.subheader(f"{case['place']} · {case['title']}")
                st.write(case["body"])
                st.link_button(case["source_title"], case["source_url"])
    st.header("读完五地，你发现了什么？", anchor="nian-discovery")
    st.write(story["discovery"])
    st.divider()
    st.caption(FULL_TITLE)
