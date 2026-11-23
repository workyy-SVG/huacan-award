"""Display the public six-character website in Streamlit Community Cloud."""

import streamlit as st

SITE_URL = "https://workyy-svg.github.io/huacan-award/"

st.set_page_config(page_title="字里寻踪", page_icon="年", layout="wide")
st.html("""
<style>
[data-testid="stMainBlockContainer"] { max-width: none; padding: 0; }
[data-testid="stHeader"] { display: none; }
[data-testid="stIFrame"] {
    width: 100%;
    height: 100dvh !important;
    border: 0;
    display: block;
}
</style>
""")
st.iframe(SITE_URL, height=860)
