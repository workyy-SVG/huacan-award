import json
import base64
from journey import render
import streamlit.components.v1 as components
from pathlib import Path

import streamlit as st


TITLE = "字里寻踪：两岸四海的生活印记"
FULL_TITLE = f"《{TITLE}——汉字与民俗故事交互设计》"
DATA_PATH = Path(__file__).parent / "data" / "nian-quanzhou-jinmen.json"
story = json.loads(DATA_PATH.read_text(encoding="utf-8"))

st.set_page_config(page_title=TITLE, page_icon="年", layout="wide")
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
    cover = base64.b64encode((DATA_PATH.parent.parent / "assets" / "cover-map.webp").read_bytes()).decode("ascii")
    st.html(f"""
<style>
[data-testid="stHeader"] {{ display:none; }}
.block-container {{ max-width:1180px; padding:clamp(18px,4vw,64px); }}
.globe-cover {{
  display:grid; grid-template-columns:1fr 1.2fr; align-items:center;
  min-height:78svh; gap:clamp(20px,4vw,64px); margin:auto;
  padding:clamp(22px,4vw,58px); background:#f9f5ed;
  border-block:1px solid #c7b9a0; color:#342f28;
}}
.globe-art {{width:100%; display:block; mix-blend-mode:multiply;}}
.globe-copy h1 {{font-size:clamp(44px,6vw,84px); color:#872e22; font-weight:700;
  letter-spacing:.04em; margin:0; padding:0; line-height:1.15;}}
.globe-copy p {{margin:16px 0 32px; font-size:clamp(16px,2vw,21px);}}
.globe-start {{display:inline-block; background:#872e22; color:white!important;
  text-decoration:none; padding:12px 23px; border-radius:5px;}}
.globe-search {{margin-top:16px; display:flex; max-width:340px; border-bottom:1px solid #998976;}}
.globe-search input,.globe-search button {{font:inherit; background:transparent; border:0; padding:12px 4px; color:#43372b;}}
.globe-search input {{min-width:0; flex:1;}}
.globe-search button {{cursor:pointer; padding-inline:12px;}}
@media(max-width:700px) {{
  .globe-cover {{grid-template-columns:1fr; min-height:auto; gap:20px;}}
  .globe-art {{max-width:480px; margin:auto;}}
}}
</style>
<main class="globe-cover">
  <div class="globe-copy"><h1>字里寻踪</h1><p>同一个字，连接不同地方的生活记录</p>
    <a class="globe-start" href="?story=nian" target="_self">选一个字，开始寻踪</a>
    <form class="globe-search" id="lookup" method="get"><input name="hanzi" placeholder="查一个我感兴趣的字" aria-label="查一个我感兴趣的字" required>
    <button type="submit">查询</button></form>
  </div>
  <img class="globe-art" src="data:image/webp;base64,{cover}" alt="折页地图，标有两岸、香港、澳门与海外华人社群">
</main>
""")
    if lookup:
        st.info("当前预览已收录「年」字，请试试输入「年」。")
else:
    if st.button("返回首页"):
        st.query_params.clear()
        st.rerun()
    st.html("""<style>
    .block-container {max-width:100%;padding:3rem .5rem 0}
    iframe[title="streamlit.components.v1.html"] {height:calc(100dvh - 7rem)}
    </style>""")
    components.html(render(story, selected if selected in case_ids else "nian-jinmen"),
                    height=800, scrolling=True)
