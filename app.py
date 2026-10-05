"""The redesigned interface for Streamlit and Streamlit Community Cloud."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from streamlit_bridge import initialize_store, dispatch

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Website Quality Checker", page_icon="◎", layout="wide")

@st.cache_resource
def backend():
    return initialize_store(ROOT)

backend()
st.markdown("""<style>
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#fff;}
[data-testid="stHeader"]{display:none;}
[data-testid="stMainBlockContainer"],.block-container{max-width:none;padding:0!important;}
[data-testid="stVerticalBlock"]{gap:0;}
iframe{display:block;border:0;}
</style>""", unsafe_allow_html=True)

# A stable key preserves the frontend while API responses arrive.
checker = components.declare_component("website_checker", path=str(ROOT / "web"))
request = checker(response=st.session_state.get("wqc_response"), key="website_checker")
if isinstance(request, dict) and request.get("id") != st.session_state.get("wqc_last_id"):
    response, cookie = dispatch(request, st.session_state.get("wqc_cookie", ""))
    st.session_state["wqc_cookie"] = cookie
    st.session_state["wqc_last_id"] = request.get("id")
    st.session_state["wqc_response"] = response
    st.rerun()
