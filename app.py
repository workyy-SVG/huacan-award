import json
import base64
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
    st.markdown('<div class="seal" aria-hidden="true">年</div>', unsafe_allow_html=True)
    st.title(story["question"])
    st.write(story["intro"])
    if selected in case_ids:
        case = next(item for item in all_cases if item["id"] == selected)
        st.caption(f"从{case['place']}出发")
    st.header("第一站 · 两岸")
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
    for section in story["extensions"]:
        st.header(section["heading"])
        st.write(section["question"])
        for case in section["cases"]:
            with st.container(border=True):
                st.subheader(f"{case['place']} · {case['title']}")
                st.write(case["body"])
                st.link_button(case["source_title"], case["source_url"])
    st.header("读完五地，你发现了什么？")
    st.write(story["discovery"])
    st.subheader("我的寻踪卡")
    choice = st.radio(
        "哪一个细节你想带走？",
        options=all_cases,
        index=next((i for i, case in enumerate(all_cases) if case["id"] == selected), 0),
        format_func=lambda case: f"{case['place']} · {case['title']}",
    )
    note = (
        f"字里寻踪 · 年\n{choice['place']}｜{choice['title']}\n"
        f"{choice['recorded_action']}\n出处：{choice['source_title']}\n{choice['source_url']}"
    )
    st.code(note, language="text")
    st.download_button("保存寻踪记录", note, "我的寻踪卡-年.txt", "text/plain")

    st.divider()
    st.caption(FULL_TITLE)
