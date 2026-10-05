"""Streamlit interface for Website Quality Checker.

Run locally with: python -m streamlit run app.py
"""
from dataclasses import asdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import base64
import hashlib
import hmac
import io
import json
import os
import zipfile
import streamlit as st
from PIL import Image
from sitecheck.models import Options
from sitecheck.network import normalize, ScanError
from sitecheck.scanner import run_scan
from sitecheck.storage import Store,compare_scans
from sitecheck.reports import csv_report,pdf_report,issue_markdown,visual_diff

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "web" / "assets"


def _font_data(name):
    path = ASSETS / name
    if not path.is_file():
        return ""
    return base64.b64encode(path.read_bytes()).decode("ascii")


OPEN_SAUCE = _font_data("OpenSauceSans-Regular.ttf")
OPEN_SAUCE_SEMI = _font_data("OpenSauceSans-SemiBold.ttf")
SPACE_MONO = _font_data("SpaceMono-Regular.ttf")
SPACE_MONO_BOLD = _font_data("SpaceMono-Bold.ttf")

st.set_page_config(
    page_title="Website Quality Checker",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f'''<style>
@font-face{{font-family:'Open Sauce';src:url(data:font/ttf;base64,{OPEN_SAUCE}) format('truetype');font-weight:400;font-display:swap}}
@font-face{{font-family:'Open Sauce';src:url(data:font/ttf;base64,{OPEN_SAUCE_SEMI}) format('truetype');font-weight:600;font-display:swap}}
@font-face{{font-family:'Space Mono';src:url(data:font/ttf;base64,{SPACE_MONO}) format('truetype');font-weight:400;font-display:swap}}
@font-face{{font-family:'Space Mono';src:url(data:font/ttf;base64,{SPACE_MONO_BOLD}) format('truetype');font-weight:700;font-display:swap}}
:root{{--accent:#787ff6;--indigo:#303596;--white:#fff;--black:#000;--tint:#f5f5fd;--line:rgba(48,53,150,.20);--muted:rgba(0,0,0,.62);--mono:'Space Mono',monospace;--heading:'Open Sauce',sans-serif}}
html,body,[class*="css"]{{font-family:var(--mono)}}
body{{background:var(--white);color:var(--black)}}
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"], #MainMenu, footer{{display:none!important}}
[data-testid="stAppViewContainer"]{{background:var(--white)}}
[data-testid="stMain"]{{background:var(--white)}}
.block-container{{max-width:1440px;padding:0 5% 5rem!important}}
[data-testid="stVerticalBlock"]{{gap:1rem}}
h1,h2,h3,h4{{font-family:var(--heading)!important;letter-spacing:-.045em!important;line-height:1.12!important}}
p,li,label,[data-testid="stCaptionContainer"]{{line-height:1.75}}
a{{color:inherit}}

.wqc-brand{{display:flex;align-items:center;gap:13px;min-height:72px;font:10px/1.35 var(--mono);letter-spacing:.05em}}
.wqc-brand svg{{width:35px;height:35px;color:var(--indigo);flex:none}}
.wqc-brand strong{{font-weight:400}}
.wqc-workspace{{font:9px/1.4 var(--mono);letter-spacing:.06em;text-align:right;padding-top:26px;white-space:nowrap}}
.wqc-workspace i{{display:inline-block;width:6px;height:6px;background:var(--indigo);margin-right:8px}}
.st-key-top_nav{{border-bottom:1px solid var(--line);padding:14px 0 10px;margin-bottom:34px}}
.st-key-top_nav [data-testid="stHorizontalBlock"]{{align-items:center;gap:.35rem}}
.st-key-top_nav [data-testid="stButton"] button{{min-height:40px!important;border-radius:2px!important;padding:8px 12px!important;font:10px/1 var(--mono)!important;letter-spacing:.03em!important;box-shadow:none!important;border:1px solid transparent!important;background:transparent!important;color:var(--black)!important}}
.st-key-top_nav [data-testid="stButton"] button:hover{{background:var(--tint)!important;border-color:var(--line)!important;color:var(--indigo)!important}}
.st-key-top_nav [data-testid="stButton"] button[kind="primary"]{{border-color:var(--indigo)!important;color:var(--indigo)!important;background:var(--white)!important}}

.wqc-kicker{{font:700 10px/1.5 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--indigo);margin-bottom:14px}}
.wqc-page-title{{font:600 clamp(40px,5vw,68px)/1.04 var(--heading);letter-spacing:-.05em;margin:0;max-width:900px}}
.wqc-page-title em{{font-style:normal;color:var(--indigo)}}
.wqc-intro{{max-width:690px;color:var(--muted);font:11px/1.9 var(--mono);margin:18px 0 28px}}
.wqc-page-head{{padding:10px 0 20px}}

.wqc-hero-copy .wqc-kicker{{margin-top:20px;margin-bottom:27px}}
.wqc-hero-title{{font:600 clamp(56px,6.3vw,92px)/1.01 var(--heading);letter-spacing:-.055em;margin:0 0 26px}}
.wqc-hero-title em{{font-style:normal;color:var(--indigo)}}
.wqc-hero-body{{max-width:455px;font:12px/1.9 var(--mono);margin:0 0 24px;color:var(--black)}}
.wqc-hero-graphic{{color:var(--indigo);max-width:470px;margin:18px 0 0 auto}}
.wqc-hero-graphic svg{{width:100%;height:auto;display:block}}
.wqc-graphic-caption{{display:flex;justify-content:space-between;border-top:1px solid var(--indigo);padding-top:12px;font:9px/1.4 var(--mono);letter-spacing:.08em}}
.wqc-hero-foot{{display:flex;flex-wrap:wrap;gap:15px;color:var(--muted);font:9px/1.5 var(--mono);margin-top:17px}}
.wqc-hero-foot span::after{{content:' / ';margin-left:15px;color:rgba(0,0,0,.3)}}
.wqc-hero-foot span:last-child::after{{content:'';margin:0}}

.wqc-inspection{{background:var(--indigo);color:var(--white);padding:42px 46px;margin:36px 0 30px;display:grid;grid-template-columns:1fr 1.1fr;gap:70px}}
.wqc-inspection .label{{font:10px/1.5 var(--mono);letter-spacing:.1em}}
.wqc-inspection h2{{font:600 clamp(32px,3.5vw,48px)/1.08 var(--heading);letter-spacing:-.045em;margin:14px 0 18px}}
.wqc-inspection p{{max-width:430px;color:rgba(255,255,255,.76);font:11px/1.8 var(--mono)}}
.wqc-inspection-list{{display:grid;align-content:center}}
.wqc-inspection-list div{{padding:14px 0;text-align:center;font:11px/1.5 var(--mono)}}
.wqc-history-strip{{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:22px 0 12px}}
.wqc-history-strip h3{{font:600 23px/1.2 var(--heading);margin:8px 0 3px}}
.wqc-history-strip p{{font-size:10px;color:var(--muted);margin:0}}

.wqc-summary{{background:var(--indigo);color:var(--white);padding:28px 30px;margin:18px 0 20px;display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
.wqc-metric{{min-height:92px;display:flex;flex-direction:column;justify-content:center;text-align:center}}
.wqc-metric strong{{font:600 42px/1 var(--heading);letter-spacing:-.04em}}
.wqc-metric span{{font:9px/1.5 var(--mono);letter-spacing:.05em;text-transform:uppercase;color:rgba(255,255,255,.72);margin-top:10px}}

[data-testid="stForm"]{{border:0!important;padding:0!important}}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"]>div>div,[data-baseweb="select"]>div,[data-testid="stNumberInput"] input{{border:1px solid var(--line)!important;border-radius:2px!important;background:var(--white)!important;box-shadow:none!important;color:var(--black)!important;font:11px/1.4 var(--mono)!important}}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus,[data-testid="stNumberInput"] input:focus{{border-color:var(--indigo)!important;box-shadow:0 0 0 2px rgba(120,127,246,.25)!important}}
[data-testid="stWidgetLabel"] p{{font:10px/1.45 var(--mono)!important}}
[data-testid="stCheckbox"] label p{{font-size:10px!important}}
[data-testid="stExpander"]{{border:1px solid var(--line)!important;border-radius:2px!important;background:var(--white)!important}}
[data-testid="stExpander"] summary{{font:10px/1.4 var(--mono)!important;letter-spacing:.02em}}
[data-testid="stExpander"] summary svg,[data-testid="stSelectbox"] svg{{display:none!important}}
[data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{{min-height:42px;border:1px solid var(--black)!important;border-radius:2px!important;background:var(--white)!important;color:var(--black)!important;box-shadow:none!important;font:10px/1.4 var(--mono)!important;padding:10px 18px!important}}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover{{background:var(--tint)!important;border-color:var(--indigo)!important;color:var(--indigo)!important}}
[data-testid="stFormSubmitButton"] button[kind="primary"],[data-testid="stButton"] button[kind="primary"]{{background:var(--black)!important;color:var(--white)!important;border-color:var(--black)!important}}
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,[data-testid="stButton"] button[kind="primary"]:hover{{background:var(--indigo)!important;border-color:var(--indigo)!important}}
[data-testid="stTabs"] [data-baseweb="tab-list"]{{gap:8px;border-bottom:1px solid var(--black)}}
[data-testid="stTabs"] button{{font:10px/1.4 var(--mono)!important}}
[data-testid="stDataFrame"], [data-testid="stTable"]{{border:1px solid var(--line);border-radius:0!important}}
[data-testid="stMetric"]{{border:0!important;background:var(--tint);padding:20px!important;border-radius:0!important;text-align:center}}
[data-testid="stMetricValue"]{{font:600 36px/1 var(--heading)!important}}
[data-testid="stMetricLabel"] p{{font-size:9px!important;text-transform:uppercase;letter-spacing:.05em}}
[data-testid="stAlert"]{{border-radius:0!important;border:0!important;border-left:3px solid var(--indigo)!important;background:var(--tint)!important;color:var(--black)!important}}
hr{{border:0!important;border-top:1px solid var(--line)!important;margin:28px 0!important}}
code,pre{{font-family:var(--mono)!important}}
.wqc-selected{{padding:10px 0 22px;margin-top:-14px}}
.wqc-selected-note{{font:9px/1.5 var(--mono);color:var(--muted);margin-top:7px}}

@media(max-width:900px){{
  .block-container{{padding:0 5% 4rem!important}}
  .st-key-top_nav [data-testid="stHorizontalBlock"]{{flex-wrap:wrap}}
  .wqc-workspace{{display:none}}
  .wqc-inspection{{grid-template-columns:1fr;gap:24px;padding:34px 28px}}
  .wqc-summary{{grid-template-columns:repeat(2,1fr)}}
  .wqc-hero-graphic{{margin:0 auto;max-width:380px}}
}}
@media(max-width:620px){{
  .wqc-brand strong{{display:none}}
  .wqc-hero-title{{font-size:54px}}
  .wqc-summary{{grid-template-columns:1fr 1fr;padding:20px 16px}}
  .wqc-metric strong{{font-size:34px}}
  .wqc-inspection{{margin-left:-2%;margin-right:-2%}}
}}
@media(prefers-reduced-motion:reduce){{*{{scroll-behavior:auto!important;transition:none!important;animation:none!important}}}}
</style>''', unsafe_allow_html=True)

password=os.environ.get("QUALITY_APP_PASSWORD","")
if password and not st.session_state.get("authenticated"):
    st.markdown('<div class="wqc-page-head"><div class="wqc-kicker">PRIVATE WORKSPACE</div><h1 class="wqc-page-title">Open your website review workspace.</h1></div>',unsafe_allow_html=True)
    with st.form("login"):
        entered=st.text_input("Workspace password",type="password")
        if st.form_submit_button("Open workspace",type="primary"):
            if hmac.compare_digest(entered,password):
                st.session_state.authenticated=True
                st.rerun()
            else:
                st.error("The password did not match.")
    st.stop()

store=Store()
reviews=store.reviews()
history=store.scans()

NAV_ITEMS=[
    ("CHECK","Scan"),("FINDINGS","Issues"),("PAGES","Pages"),("COMPARE","Compare"),
    ("REPORTS","Reports"),("SCHEDULES","Schedules"),("SETTINGS","Settings"),("HELP","Help"),
]

with st.sidebar:
    nav=st.radio("Workspace",[v for _,v in NAV_ITEMS],label_visibility="collapsed",key="navigation")


def _goto(section):
    st.session_state.navigation=section


def render_top_nav(current):
    with st.container(key="top_nav"):
        cols=st.columns([2.25,1,1.05,.9,1.05,1.05,1.25,1.15,.75,1.65],gap="small")
        cols[0].markdown('''<div class="wqc-brand"><svg viewBox="0 0 44 44" aria-hidden="true"><path d="M5 17h23v23H5zM5 17 17 5h23v23L28 40M28 17 40 5M28 17v23M17 5v23H5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M28 17 40 5v23L28 40z" fill="currentColor"/></svg><strong>WEBSITE QUALITY<br>CHECKER</strong></div>''',unsafe_allow_html=True)
        for col,(label,target) in zip(cols[1:9],NAV_ITEMS):
            col.button(label,key=f"nav_{target.lower()}",type="primary" if current==target else "secondary",use_container_width=True,on_click=_goto,args=(target,))
        cols[9].markdown('<div class="wqc-workspace"><i></i>LOCAL WORKSPACE</div>',unsafe_allow_html=True)


render_top_nav(nav)

scan=None
if history:
    if nav in {"Issues","Pages","Reports","Schedules"}:
        chosen=st.selectbox(
            "Selected analysis",
            [h["id"] for h in history],
            format_func=lambda sid:next(h["created"][:16].replace("T"," ")+" / "+urlsplit(h["url"]).netloc for h in history if h["id"]==sid),
            key="chosen_scan",
        )
        scan=store.scan(chosen)
        st.markdown(f'<div class="wqc-selected-note">{len(scan["pages"])} pages / {len(scan["issues"])} findings</div>',unsafe_allow_html=True)
    else:
        selected=st.session_state.get("chosen_scan")
        ids={h["id"] for h in history}
        if selected not in ids:
            selected=history[0]["id"]
        scan=store.scan(selected)


def title(kicker,heading,body=""):
    heading_html=escape(heading).replace("\\n","<br>")
    body_html=f'<div class="wqc-intro">{escape(body)}</div>' if body else ""
    st.markdown(f'<div class="wqc-page-head"><div class="wqc-kicker">{escape(kicker)}</div><h1 class="wqc-page-title">{heading_html}</h1>{body_html}</div>',unsafe_allow_html=True)


def summary(data):
    values=[
        (len(data["pages"]),"Pages inspected"),
        (sum(i["severity"]=="Needs fixing" for i in data["issues"]),"Needs fixing"),
        (sum(i["severity"]=="Review" for i in data["issues"]),"Review"),
        (sum(i["severity"]=="Couldn't verify" for i in data["issues"]),"Couldn't verify"),
    ]
    html=''.join(f'<div class="wqc-metric"><strong>{n}</strong><span>{escape(label)}</span></div>' for n,label in values)
    st.markdown(f'<div class="wqc-summary">{html}</div>',unsafe_allow_html=True)
    if not data.get("complete",False):
        st.info("Partial coverage: review the scan notes before drawing conclusions.")


def geometric_hero():
    return '''<div class="wqc-hero-graphic"><svg viewBox="0 0 440 425" role="img" aria-label="Interconnected wireframe cubes representing a website"><path d="M55 18H404V396H20V100H55V18M404 240V286M404 308V354" fill="none" stroke="currentColor" stroke-width=".8"/><path d="M16 386h35M20 369v35M388 15v16M380 23h16" stroke="currentColor" stroke-width=".8"/><g transform="translate(1,30)"><path d="M0 61h74v282H0zM0 61 37 24h74v282L74 343M74 61l37-37M37 24v282H0" stroke="currentColor" fill="none" stroke-width="1"/><path d="M74 61 111 24v282l-37 37z" fill="currentColor"/></g><g transform="translate(129,46)"><circle cx="49" cy="55" r="45" fill="none" stroke="currentColor"/><circle cx="73" cy="31" r="45" fill="currentColor"/><circle cx="49" cy="55" r="45" fill="white"/><path d="M73-14a45 45 0 0 0-45 45 45 45 0 0 0 45 45" fill="none" stroke="currentColor"/></g><g transform="translate(268,36)"><path d="M12 44h64v64H12zM12 44 44 12h64v64L76 108M76 44l32-32M44 12v64H12" fill="none" stroke="currentColor"/><path d="M76 44 108 12v64l-32 32z" fill="currentColor"/></g><g transform="translate(132,168)"><path d="M12 44h64v64H12zM12 44 44 12h64v64L76 108M76 44l32-32M44 12v64H12" fill="none" stroke="currentColor"/><path d="M76 44 108 12v64l-32 32z" fill="currentColor"/></g><g transform="translate(268,168)"><path d="M12 44h64v64H12zM12 44 44 12h64v64L76 108M76 44l32-32M44 12v64H12" fill="none" stroke="currentColor"/><path d="M76 44 108 12v64l-32 32z" fill="currentColor"/></g><g transform="translate(132,298)"><path d="M12 44h64v64H12zM12 44 44 12h64v64L76 108M76 44l32-32M44 12v64H12" fill="none" stroke="currentColor"/><path d="M76 44 108 12v64l-32 32z" fill="currentColor"/></g><g transform="translate(268,298)"><path d="M12 44h64v64H12zM12 44 44 12h64v64L76 108M76 44l32-32M44 12v64H12" fill="none" stroke="currentColor"/><path d="M76 44 108 12v64l-32 32z" fill="currentColor"/></g></svg><div class="wqc-graphic-caption"><span>STRUCTURE&nbsp;&nbsp;SIGNAL&nbsp;&nbsp;ACTION</span><span>FIG. 01</span></div></div>'''

def execute(url,options):
    message=st.empty()
    try:
        with st.spinner("Checking the website…"):
            result=run_scan(url,options,progress=message.info,artifact_dir=store.artifacts)
            data=store.save_scan(result)
        message.empty()
        st.session_state["latest_completed"]=data["id"]
        st.success(f"Scan saved: {len(data['pages'])} pages and {len(data['issues'])} findings. Open Issues to review.")
        # The latest scan becomes the default selector on the next rerun.
        st.session_state.pop("chosen_scan",None)
        st.rerun()
    except Exception as exc:
        message.empty()
        st.error("The scan could not finish: "+str(exc))


def image_path(path):
    if not path:
        return None
    path=Path(path).resolve()
    return path if path.is_relative_to(store.root) and path.is_file() else None


def require_scan():
    if not scan:
        st.info("Run a scan or load the sample from Scan to use this view.")
        st.stop()


def lines(value):
    return [s.strip() for s in value.splitlines() if s.strip()]


if nav=="Scan":
    hero_left,hero_right=st.columns([1.15,1],gap="large")
    with hero_left:
        st.markdown('''<div class="wqc-hero-copy"><div class="wqc-kicker">WEBSITE ANALYSIS / BUILT TO INSPECT</div><h1 class="wqc-hero-title">Know your<br>website.<br><em>Inside out.</em></h1><p class="wqc-hero-body">Look closer at the details that make a website work. Check its structure, find the issues, and turn real findings into useful next steps.</p></div>''',unsafe_allow_html=True)
        with st.form("scan_form"):
            url=st.text_input("ENTER YOUR WEBSITE",placeholder="https://your-website.com")
            c1,c2=st.columns(2)
            profile=c1.selectbox("Scan profile",["Business website","Portfolio","Online store","Blog","Custom"])
            limit=c2.selectbox("Pages to inspect",[1,5,10,20,30],index=1)
            browser=st.checkbox("Include browser previews",help="Requires Chromium. Captures desktop, mobile, print, focus and reduced-motion previews.")
            with st.expander("SCAN SETTINGS / CHECKS AND LIMITS"):
                categories=st.multiselect("Check categories",Options().categories,default=Options().categories)
                a,b,c=st.columns(3)
                requests=a.slider("Maximum requests",20,500,150,10)
                seconds=b.slider("Time budget (seconds)",30,600,180,30)
                image_kb=c.number_input("Large image threshold (KB)",100,10000,500,100)
                a,b,c=st.columns(3)
                browser_pages=a.slider("Pages with browser previews",1,5,2)
                spelling=b.checkbox("Check spelling")
                form_checks=c.checkbox("Inspect form validity states",help="Reads native browser validity. Does not fill or submit forms.")
                language=st.selectbox("Spelling language",["en","es","fr","de","pt","it"])
                st.caption("Blog and online-store profiles enable spelling; portfolio uses a tighter 350 KB image threshold. Explicit categories still control source checks.")
            with st.expander("BRAND RULES / PAGE JOURNEY"):
                defaults=store.setting("brand_rules",{})
                dictionary=st.text_area("Allowed dictionary words (one per line)","\n".join(defaults.get("dictionary",[])))
                required=st.text_area("Phrases required on each page (one per line)","\n".join(defaults.get("required_phrases",[])))
                forbidden=st.text_area("Outdated wording to find (one per line)","\n".join(defaults.get("forbidden_phrases",[])))
                journey=st.text_area("Check this journey: URLs or paths in order",placeholder="/\n/services\n/booking",help="Checks URL reachability and links between steps. Browser mode adds previews. Does not click through transactions.")
            consent=st.checkbox("I own this website or have permission to review it.")
            submitted=st.form_submit_button("RUN CHECK",type="primary",use_container_width=True)
        st.markdown('<div class="wqc-hero-foot"><span>PUBLIC WEBSITES</span><span>READ-ONLY CHECKS</span><span>NO AI KEY NEEDED</span></div>',unsafe_allow_html=True)
    with hero_right:
        st.markdown(geometric_hero(),unsafe_allow_html=True)

    if submitted:
        if not consent:
            st.warning("Confirm permission before starting the scan.")
        elif not url.strip():
            st.warning("Enter the website URL.")
        else:
            options=Options(max_pages=limit,max_requests=requests,max_seconds=seconds,image_kb=min(image_kb,350) if profile=="Portfolio" else image_kb,browser=browser,browser_pages=browser_pages,spelling=spelling or profile in ("Blog","Online store"),language=language,profile=profile,dictionary=lines(dictionary),required_phrases=lines(required),forbidden_phrases=lines(forbidden),journey=lines(journey),form_checks=form_checks,categories=categories)
            execute(url,options)

    st.markdown('''<section class="wqc-inspection"><div><span class="label">THE INSPECTION SYSTEM</span><h2>A website is more<br>than its first impression.</h2><p>Inspect the details behind the interface. Clear evidence tells you where to look. Practical recommendations help you decide what to fix.</p></div><div class="wqc-inspection-list"><div>Links &amp; destinations</div><div>Page structure &amp; accessibility signals</div><div>Images &amp; content</div><div>Metadata &amp; technical checks</div><div>Browser previews, when enabled</div></div></section>''',unsafe_allow_html=True)

    history_copy,history_action=st.columns([4,1],vertical_alignment="center")
    history_copy.markdown('<div class="wqc-history-strip"><div><div class="wqc-kicker" style="margin-bottom:0">YOUR WORKSPACE</div><h3>Keep the fixes in view.</h3><p>Saved scans, review notes, comparisons, and reports.</p></div></div>',unsafe_allow_html=True)
    if history_action.button("Explore a sample report",use_container_width=True):
        from sitecheck.demo import create_demo
        store.save_scan(create_demo())
        st.session_state.pop("chosen_scan",None)
        st.rerun()

    if scan:
        st.divider()
        title("Selected analysis","Your latest saved scan.",scan["url"])
        summary(scan)
        with st.expander("SCOPE AND SCAN NOTES"):
            for note in scan["notes"]:
                st.write("• "+note)
            st.json(scan["options"],expanded=False)

elif nav=="Issues":
    title("Review & resolve","Small fixes. Better experience.","Each finding includes evidence and a suggested next step. Save ownership, deadlines and decisions as you work.")
    require_scan()
    summary(scan)
    a,b,c=st.columns(3)
    severity=a.multiselect("Result",["Needs fixing","Review","Couldn't verify"],default=["Needs fixing","Review","Couldn't verify"])
    category=b.multiselect("Category",sorted({i["category"] for i in scan["issues"]}))
    query=c.text_input("Find a page or issue")
    statuses=["Open","In progress","Fixed (manual)","Intentional","Needs review"]
    selected_status=st.multiselect("Work status",statuses)
    filtered=[i for i in scan["issues"] if i["severity"] in severity and (not category or i["category"] in category) and (not query or query.lower() in json.dumps(i).lower()) and (not selected_status or reviews.get(i["id"],{}).get("status","Open") in selected_status)]
    blockers=[i for i in scan["issues"] if reviews.get(i["id"],{}).get("blocker") and reviews.get(i["id"],{}).get("status") not in ("Fixed (manual)","Intentional")]
    if blockers:
        st.warning(f"{len(blockers)} open finding(s) marked as launch blockers by your team.")
    st.caption(f"{len(filtered)} findings shown")
    for issue in filtered[:100]:
        rid=issue["id"]
        review=reviews.get(rid,{})
        with st.expander(f"{issue['severity']} / {issue['title']} / {urlsplit(issue['page']).path}"):
            st.text(issue["page"])
            st.markdown("**What was found**")
            st.write(issue["evidence"])
            st.markdown("**Suggested action**")
            st.write(issue["fix"])
            if issue["target"]:
                st.code(issue["target"],language=None)
            with st.form("review-"+rid):
                a,b,c=st.columns(3)
                status=a.selectbox("Status",statuses,index=statuses.index(review.get("status","Open")))
                owner=b.text_input("Owner",review.get("owner",""))
                due=c.text_input("Due date",review.get("due",""),placeholder="YYYY-MM-DD")
                blocker=st.checkbox("Must resolve before launch",review.get("blocker",False))
                notes=st.text_area("Notes / reason for an exception",review.get("notes",""))
                evidence=st.file_uploader("Attach a screenshot",type=["png","jpg","jpeg"])
                if st.form_submit_button("Save review"):
                    payload={"status":status,"owner":owner,"due":due,"blocker":blocker,"notes":notes,"attachment":review.get("attachment","")}
                    if status=="Intentional" and not notes.strip():
                        st.warning("Add a reason for the intentional exception.")
                    else:
                        try:
                            if evidence:
                                img=Image.open(evidence);img.thumbnail((2400,2400))
                                path=store.artifacts/(rid+"-attachment.png")
                                img.convert("RGB").save(path)
                                payload["attachment"]=str(path)
                            store.review(rid,payload)
                            st.rerun()
                        except Exception as exc:
                            st.error("Could not save the attachment: "+str(exc))
            attachment=image_path(review.get("attachment"))
            if attachment:
                st.image(str(attachment),caption="Attached review evidence",width=600)
            a,b=st.columns(2)
            a.download_button("Download issue card",issue_markdown(issue,review),file_name=f"issue-{rid}.md",mime="text/markdown",key="card-"+rid)
            if b.button("Recheck this page",key="recheck-"+rid):
                settings={**scan["options"],"max_pages":1,"journey":[]}
                execute(issue["page"],Options(**settings))
    if not filtered:
        st.info("No findings match these filters. This does not certify that the website is issue-free.")

elif nav=="Pages":
    title("Inspect the details","Every page has a story.","Explore page connections, previews, resources and the checks that need your judgment.")
    require_scan()
    if not scan["pages"]:
        st.info("No HTML pages were available to inspect. Review Issues for the failure reason.")
        st.stop()
    page=st.selectbox("Page",scan["pages"],format_func=lambda p:p["url"])
    tab1,tab2,tab3,tab4=st.tabs(["Page & previews","Site map","Resources & speed","Manual review"])
    with tab1:
        st.subheader(page["title"] or "Untitled page")
        st.write(page["description"] or "No meta description")
        a,b,c=st.columns(3)
        a.metric("Click depth",page["depth"])
        b.metric("HTML download",f"{page['html_bytes']/1024:.0f} KB")
        c.metric("Fetch time",f"{page['response_seconds']:.2f} s")
        st.caption("Fetch time is a single server-side observation, not a page-speed score.")
        shots=page.get("browser",{}).get("screenshots",{})
        available={k:image_path(v) for k,v in shots.items() if image_path(v)}
        if available:
            mode=st.radio("Preview",list(available),horizontal=True)
            st.image(str(available[mode]),caption=mode,use_container_width=True)
            st.download_button("Download screenshot",available[mode].read_bytes(),available[mode].name,"image/png")
        else:
            st.info("No browser preview for this page. Enable browser previews and install Chromium to capture it.")
        for note in page.get("browser",{}).get("limitations",[]):
            st.caption(note)
        st.subheader("Social sharing fields")
        social=page["social"]
        with st.container(border=True):
            st.caption(urlsplit(page["url"]).netloc.upper())
            st.markdown("**"+(social.get("og:title") or page["title"] or "Missing title")+"**")
            st.write(social.get("og:description") or "Missing social description")
            st.text("Image: "+(social.get("og:image") or "Not set"))
        st.caption("Metadata preview only. Platforms may crop or cache content differently.")
        with st.expander("Headings, forms and browser observations"):
            st.json({"headings":page["headings"],"forms":page["forms"],"browser":page.get("browser",{})})
    with tab2:
        st.caption("Select a page above to explore its connections. Only links found in scanned HTML are shown.")
        import graphviz
        graph=graphviz.Digraph()
        graph.attr(rankdir="TB",bgcolor="transparent")
        urls={p["url"] for p in scan["pages"]}
        for p in scan["pages"]:
            graph.node(p["url"],label=urlsplit(p["url"]).path or "/",style="filled",fillcolor="#CBDCD0" if p["url"]==page["url"] else "#EDF0EB",shape="box")
        for src,dst in sorted({(l["from"],l["to"]) for l in scan["links"] if l["to"] in urls}):
            graph.edge(src,dst)
        st.graphviz_chart(graph,use_container_width=True)
        st.dataframe([{k:l.get(k) for k in ("from","to","label","result")} for l in scan["links"] if page["url"] in (l["from"],l["to"])],use_container_width=True,hide_index=True)
        st.subheader("Journey reachability")
        if scan["journey"]:
            st.dataframe([{k:v for k,v in step.items() if k!="screenshots"} for step in scan["journey"]],hide_index=True,use_container_width=True)
        else:
            st.caption("Add a sequence of paths under Scan / Brand rules and page journey.")
    with tab3:
        resources=[r for r in scan["resources"] if r["page"]==page["url"]]
        st.metric("Resources found in HTML",len(resources))
        st.dataframe([{k:r.get(k) for k in ("kind","url","status","bytes","seconds","result")} for r in resources],hide_index=True,use_container_width=True)
        st.caption("HTML-discovered resources only. JavaScript, CSS imports, caching and user location can change real download totals.")
    with tab4:
        manual_key="manual-"+hashlib.sha256(page["url"].encode()).hexdigest()[:20]
        saved=store.setting(manual_key,{})
        checks=["Keyboard focus is visible and follows a sensible order","Menus and dialogs work with keyboard and Escape","No keyboard trap blocks navigation","Forms explain required fields and errors","Controlled form test shows the expected success state","Mobile content is readable and important controls are reachable","Popups are dismissible and do not hide essential content","Print view preserves important information","Reduced-motion behavior is appropriate","Policy links, business details and claims have been reviewed"]
        st.caption("Record your own inspection. Test form submissions only on an authorized test environment; this app does not submit them.")
        with st.form("manual-review"):
            answers={}
            for text in checks:
                choices=["Not reviewed","Pass","Needs work","Not applicable"]
                answers[text]=st.selectbox(text,choices,index=choices.index(saved.get(text,"Not reviewed")))
            answers["notes"]=st.text_area("Review notes",saved.get("notes",""))
            if st.form_submit_button("Save checklist"):
                store.set_setting(manual_key,answers)
                st.success("Checklist saved.")

elif nav=="Compare":
    title("Before & after","See what changed.","Compare findings and screenshots. A missing finding can reflect a changed scan scope, so keep the coverage notes in view.")
    if len(history)<2:
        st.info("Save two scans of a website to compare them.")
        st.stop()
    a,b=st.columns(2)
    first=a.selectbox("Earlier scan",history,index=1,format_func=lambda h:h["created"]+" / "+h["url"],key="before")
    second=b.selectbox("Later scan",history,index=0,format_func=lambda h:h["created"]+" / "+h["url"],key="after")
    before,after=store.scan(first["id"]),store.scan(second["id"])
    result=compare_scans(before,after)
    if before["url"]!=after["url"]:
        st.warning("These scans use different starting URLs. Compare the scope carefully.")
    if not result["comparable"]:
        st.info("Coverage or options differ, or the later scan was incomplete. 'Not seen' does not mean fixed.")
    cols=st.columns(3)
    for col,key,label in zip(cols,["new","persistent","not_seen"],["New findings","Still present","Not seen this time"]):
        col.metric(label,len(result[key]))
        with col.expander("View findings"):
            st.dataframe([{k:i[k] for k in ("title","page","severity")} for i in result[key]],hide_index=True)
    shared=sorted({p["url"] for p in before["pages"]}&{p["url"] for p in after["pages"]})
    if shared:
        target=st.selectbox("Visual comparison page",shared)
        old=next(p for p in before["pages"] if p["url"]==target).get("browser",{}).get("screenshots",{})
        new=next(p for p in after["pages"] if p["url"]==target).get("browser",{}).get("screenshots",{})
        modes=[k for k in old if k in new and image_path(old[k]) and image_path(new[k])]
        if modes:
            mode=st.selectbox("Screenshot type",modes)
            a,b=st.columns(2)
            a.image(old[mode],caption="Before",use_container_width=True)
            b.image(new[mode],caption="After",use_container_width=True)
            data,ratio=visual_diff(old[mode],new[mode])
            st.image(data,caption=f"Changed pixels highlighted / {ratio:.1%}. Dynamic content, timing and fonts can cause differences.",use_container_width=True)
            st.download_button("Download highlighted comparison",data,"visual-comparison.png","image/png")
        else:
            st.caption("Matching browser screenshots are needed for a visual comparison.")

elif nav=="Reports":
    title("Ready to hand over","Turn findings into next steps.","Download a review report, a spreadsheet of issues, or a project archive to keep with your client work.")
    require_scan()
    summary(scan)
    brand=st.text_input("Report heading",store.setting("report_brand","Website Quality Checker"))
    logo=image_path(store.setting("report_logo",""))
    if st.button("Prepare PDF report",type="primary"):
        st.session_state["pdf_export"]={"id":scan["id"],"brand":brand,"data":pdf_report(scan,reviews,brand,str(logo) if logo else None)}
    export=st.session_state.get("pdf_export",{})
    if export.get("id")==scan["id"] and export.get("brand")==brand:
        st.download_button("Download PDF",export["data"],"website-review.pdf","application/pdf")
    st.download_button("Download findings CSV",csv_report(scan,reviews),"website-findings.csv","text/csv")
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("scan.json",json.dumps(scan,indent=2))
        z.writestr("reviews.json",json.dumps({i["id"]:reviews.get(i["id"],{}) for i in scan["issues"]},indent=2))
        z.writestr("findings.csv",csv_report(scan,reviews))
        manual={}
        for p in scan["pages"]:
            manual_key="manual-"+hashlib.sha256(p["url"].encode()).hexdigest()[:20]
            manual[p["url"]]=store.setting(manual_key,{})
            for path in p.get("browser",{}).get("screenshots",{}).values():
                file=image_path(path)
                if file:
                    z.write(file,"screenshots/"+file.name)
        z.writestr("manual-checklists.json",json.dumps(manual,indent=2))
        for issue in scan["issues"]:
            z.writestr("issue-cards/"+issue["id"]+".md",issue_markdown(issue,reviews.get(issue["id"],{})))
            file=image_path(reviews.get(issue["id"],{}).get("attachment"))
            if file:
                z.write(file,"evidence/"+file.name)
    st.download_button("Download scan archive",archive.getvalue(),"website-review-archive.zip","application/zip")
    st.caption("The archive contains extracted page text and screenshots. Review its contents before sharing.")

elif nav=="Schedules":
    title("Keep an eye on it","Make review a habit.","Save a daily or weekly scan. A separate worker runs it while your machine or server stays on.")
    heartbeat=store.setting("worker_heartbeat")
    active=heartbeat and (datetime.now(timezone.utc)-datetime.fromisoformat(heartbeat)).total_seconds()<90
    if active:
        st.success("The scheduler worker recently checked in.")
    else:
        st.warning("Scheduler worker is not currently reporting. Saved schedules will wait until it is running.")
        st.code("python worker.py",language="bash")
    if scan:
        with st.form("schedule"):
            st.write("Use this scan's URL and options: "+scan["url"])
            every=st.selectbox("Repeat",[24,168],format_func=lambda h:"Daily" if h==24 else "Weekly")
            if st.form_submit_button("Save recurring scan"):
                if ".test" in urlsplit(scan["url"]).hostname:
                    st.warning("Sample reports cannot be scheduled. Run a real scan first.")
                else:
                    store.schedule(scan["url"],every,scan["options"])
                    st.rerun()
    for job in store.schedules():
        with st.container(border=True):
            st.write(job["url"])
            st.caption(f"Every {job['hours']} hours / next run {job['next_run']} UTC")
            enabled=st.checkbox("Enabled",bool(job["enabled"]),key="schedule-"+str(job["id"]))
            if enabled != bool(job["enabled"]):
                store.toggle_schedule(job["id"],enabled)
                st.rerun()
    st.subheader("Notifications")
    for n in store.notifications():
        st.write(n["message"])
        st.caption(n["created"])
    if st.button("Mark notifications read"):
        store.mark_read()
    st.caption("Notifications stay inside this workspace. Email and messaging integrations are not configured.")

elif nav=="Settings":
    title("Your workspace","Make it yours.","Set reusable brand rules and report branding. Saved data belongs to this installation.")
    with st.form("settings"):
        brand=st.text_input("Default report heading",store.setting("report_brand","Website Quality Checker"))
        logo=st.file_uploader("Report logo (PNG or JPG)",type=["png","jpg","jpeg"])
        defaults=store.setting("brand_rules",{})
        dictionary=st.text_area("Custom dictionary (one word per line)","\n".join(defaults.get("dictionary",[])))
        required=st.text_area("Required phrases (one per line)","\n".join(defaults.get("required_phrases",[])))
        forbidden=st.text_area("Outdated wording (one per line)","\n".join(defaults.get("forbidden_phrases",[])))
        if st.form_submit_button("Save settings",type="primary"):
            try:
                if logo:
                    img=Image.open(logo);img.thumbnail((1200,1200))
                    path=store.artifacts/"report-logo.png";img.convert("RGB").save(path)
                    store.set_setting("report_logo",str(path))
                store.set_setting("report_brand",brand)
                store.set_setting("brand_rules",{"dictionary":lines(dictionary),"required_phrases":lines(required),"forbidden_phrases":lines(forbidden)})
                st.success("Settings saved.")
            except Exception as exc:
                st.error("Could not save settings: "+str(exc))
    st.subheader("Setup notes")
    st.write("Start with a one-page scan. Browser checks require a separate Chromium installation. Scheduling requires the worker process and persistent disk storage.")
    st.code("python -m playwright install chromium",language="bash")
    st.write("The app binds to localhost by default. Before hosting it for others, add deployment authentication, request limits and durable storage. All trusted workspace users can see its scans and notes.")

elif nav=="Help":
    title("About the checks","Evidence first. Judgment still matters.","This workspace combines automated source checks with optional browser observations and your own manual review. It does not invent a quality score or certify accessibility, security, privacy, or legal compliance.")
    left,right=st.columns(2,gap="large")
    with left:
        st.subheader("What it checks")
        st.write("Broken or unverified destinations, page structure and accessibility signals, images and content, metadata, selected technical observations, and optional browser previews.")
        st.subheader("What stays manual")
        st.write("Keyboard behavior, forms, mobile usability, visual judgment, policy accuracy, business claims, and context-specific compliance decisions still need human review.")
    with right:
        st.subheader("Data & use")
        st.write("URLs, extracted page text, findings, screenshots, notes, and saved reviews are stored in this installation. Target websites receive scan requests. No analytics or external AI service is added by this project.")
        st.subheader("Safer use")
        st.write("Scan public pages you own or are authorized to review. Automated findings are advisory and may be incomplete, especially on JavaScript-heavy or bot-protected websites.")
    st.markdown('''<section class="wqc-inspection" style="margin-top:26px"><div><span class="label">DESIGN SYSTEM</span><h2>Built to inspect,<br>not to decorate.</h2><p>The Streamlit version now uses the same Open Sauce and Space Mono typography, indigo/periwinkle palette, cube geometry, and evidence-first visual hierarchy as the bundled custom frontend.</p></div><div class="wqc-inspection-list"><div>#787FF6 / accent</div><div>#303596 / indigo</div><div>Open Sauce / headings</div><div>Space Mono / interface copy</div><div>Reduced-motion friendly</div></div></section>''',unsafe_allow_html=True)
