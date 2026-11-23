"""Run the published six-character site inside Streamlit."""
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import declare_component

st.set_page_config(page_title="字里寻踪", page_icon="年", layout="wide")
st.html("""
<style>
[data-testid="stMainBlockContainer"] { max-width:none; padding:0; }
[data-testid="stHeader"] { display:none; }
iframe[title$=".zili_site"] { width:100%; height:100dvh !important; border:0; }
</style>
""")
site = declare_component("zili_site", path=str(Path(__file__).resolve().parent))
site(key="zili_site")
