"""
Main entry point — Streamlit-based chat UI for the APEX AI Agent.
Run with: streamlit run main.py
"""
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from agent.core import AIAgent
from utils.logger import log

# Ensure required directories exist
for _dir in ("uploads", "outputs", "logs"):
    Path(_dir).mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="APEX AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# MOBILE-RESPONSIVE CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Root variables ── */
:root {
    --primary: #111111;
    --primary-dark: #000000;
    --bg: #FFFFFF;
    --surface: #F4F4F8;
    --surface2: #EEEEF5;
    --border: #D8D8E8;
    --text: #1a1a2e;
    --text-muted: #6b6b8a;
    --user-bubble: #2a2a2a;
    --bot-bubble: #F8F8FC;
    --radius: 16px;
    --radius-sm: 10px;
}

/* ── Base reset ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stVerticalBlock"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Hide Streamlit default chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
[data-testid="collapsedControl"] {
    color: var(--text) !important;
    background: var(--surface) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
}

/* ── Main container padding ── */
.main .block-container {
    padding: 1rem 1rem 5rem 1rem !important;
    max-width: 860px !important;
    margin: 0 auto !important;
}

/* ── Logo bar ── */
.apex-logo-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 4px;
    margin-bottom: 0.6rem;
    border-bottom: 1px solid var(--border);
}
.apex-logo-icon {
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.apex-logo-text {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.01em;
}
.apex-logo-text span {
    color: var(--primary);
}

/* ── Upload indicator badge ── */
.file-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,0,0,0.06);
    border: 1px solid var(--primary);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: var(--primary);
    margin-bottom: 0.8rem;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    border-radius: var(--radius) !important;
    padding: 14px 16px !important;
    margin-bottom: 10px !important;
    border: 1px solid var(--border) !important;
    background: var(--bot-bubble) !important;
    max-width: 100% !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(0,0,0,0.04) 0%, rgba(0,0,0,0.02) 100%) !important;
    border-color: rgba(0,0,0,0.14) !important;
}
[data-testid="stChatMessage"] p {
    font-size: clamp(0.88rem, 3vw, 1rem) !important;
    line-height: 1.65 !important;
    color: var(--text) !important;
}
[data-testid="stChatMessage"] code {
    font-size: clamp(0.78rem, 2.5vw, 0.88rem) !important;
    background: rgba(0,0,0,0.06) !important;
    color: #333333 !important;
    border-radius: 5px !important;
    padding: 1px 5px !important;
}
[data-testid="stChatMessage"] pre {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    background: #f8f8fc !important;
    overflow-x: auto !important;
}

/* ── Chat input bar ── */
[data-testid="stChatInput"] {
    background: #fff !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 6px 16px !important;
    transition: border-color 0.2s !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(0,0,0,0.12) !important;
}
[data-testid="stChatInput"] textarea {
    font-size: clamp(0.9rem, 3vw, 1rem) !important;
    color: var(--text) !important;
    background: transparent !important;
}
[data-testid="stChatInput"] button {
    background: var(--primary) !important;
    border-radius: 50% !important;
    min-width: 36px !important;
    min-height: 36px !important;
}

/* ── Spinner text ── */
[data-testid="stSpinner"] p {
    font-size: 0.9rem !important;
    color: var(--primary) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #F4F4F8 !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 1.2rem 1rem !important;
}
[data-testid="stSidebar"] h1 {
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    color: var(--primary) !important;
}
[data-testid="stSidebar"] h3 {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-top: 1rem !important;
}

/* ── Sidebar buttons (quick commands) ── */
[data-testid="stSidebar"] .stButton > button {
    background: #fff !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-size: clamp(0.75rem, 2.5vw, 0.82rem) !important;
    padding: 10px 10px !important;
    min-height: 44px !important;
    text-align: left !important;
    transition: all 0.15s !important;
    width: 100% !important;
    margin-bottom: 4px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
    color: white !important;
    transform: translateX(2px) !important;
}

/* ── Clear button ── */
[data-testid="stSidebar"] .stButton:last-of-type > button {
    background: rgba(239,68,68,0.1) !important;
    border-color: rgba(239,68,68,0.4) !important;
    color: #f87171 !important;
}
[data-testid="stSidebar"] .stButton:last-of-type > button:hover {
    background: rgba(239,68,68,0.25) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius-sm) !important;
    padding: 12px !important;
    background: #fff !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--primary) !important;
}
[data-testid="stFileUploader"] label {
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
}

/* ── Success/info alerts ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    font-size: 0.85rem !important;
    padding: 10px 14px !important;
}

/* ── Capability list in sidebar ── */
.cap-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-top: 8px;
}
.cap-item {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 0.75rem;
    color: var(--text-muted);
    text-align: center;
}

/* ── Welcome card (shown when no messages) ── */
.welcome-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1.2rem 1.5rem 1rem;
    text-align: center;
    background: #F4F4F8;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin: 0.4rem 0 0.8rem;
}
.welcome-card .big-icon { font-size: 2rem; margin-bottom: 0.4rem; }
.welcome-card h2 {
    font-size: clamp(0.95rem, 3vw, 1.1rem) !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    margin-bottom: 0.25rem !important;
}
.welcome-card p {
    color: var(--text-muted) !important;
    font-size: clamp(0.78rem, 2.5vw, 0.85rem) !important;
    max-width: 420px;
    margin: 0 !important;
}
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-top: 1.2rem;
}
.chip {
    background: rgba(0,0,0,0.06);
    border: 1px solid rgba(0,0,0,0.15);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: clamp(0.72rem, 2.5vw, 0.82rem);
    color: var(--primary);
    cursor: pointer;
    transition: background 0.15s;
}
.chip:hover { background: rgba(0,0,0,0.12); }

/* ── Mobile breakpoints ── */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.6rem 0.5rem 5rem 0.5rem !important;
    }
    .apex-logo-bar { padding: 8px 4px; }
    [data-testid="stChatMessage"] { padding: 10px 12px !important; }
    .cap-list { grid-template-columns: 1fr; }
    [data-testid="stSidebar"] { width: 85vw !important; }
}

@media (max-width: 480px) {
    .apex-logo-icon { width: 32px; height: 32px; font-size: 1rem; }
    .apex-logo-text { font-size: 1rem; }
    .chip { font-size: 0.7rem; padding: 4px 10px; }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f0f0f8; }
::-webkit-scrollbar-thumb { background: #c8c8de; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }

/* ── Welcome chip buttons (light mode) ── */
[data-testid="stMain"] div[data-testid="column"] .stButton > button {
    background: rgba(0,0,0,0.04) !important;
    color: var(--primary) !important;
    border: 1.5px solid rgba(0,0,0,0.15) !important;
    border-radius: 24px !important;
    font-size: clamp(0.75rem, 2.5vw, 0.85rem) !important;
    padding: 10px 8px !important;
    min-height: 44px !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}
[data-testid="stMain"] div[data-testid="column"] .stButton > button:hover {
    background: var(--primary) !important;
    color: #fff !important;
    border-color: var(--primary) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.20) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "agent" not in st.session_state:
    try:
        st.session_state.agent = AIAgent()
    except ValueError as e:
        st.error(f"⚠️ **Setup required:** {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ **Failed to initialize agent:** {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

if "quick_command" not in st.session_state:
    st.session_state.quick_command = None

if "active_mode" not in st.session_state:
    st.session_state.active_mode = None

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 🤖 APEX Agent")
    st.caption("Multi-Capability AI • Powered by Claude")

    st.markdown("---")
    st.subheader("📁 File Upload")
    uploaded_file = st.file_uploader(
        "Drop any file here",
        type=[
            "pdf", "docx", "xlsx", "pptx", "txt", "md", "csv",
            "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp",
            "html", "py", "js", "ts", "java", "cs", "cpp", "go", "rs",
        ],
        label_visibility="collapsed",
    )

    if uploaded_file:
        file_path = f"uploads/{uploaded_file.name}"
        with open(file_path, "wb") as fh:
            fh.write(uploaded_file.getbuffer())
        st.session_state.uploaded_file_path = file_path
        st.success(f"✅ {uploaded_file.name}")
        log.info(f"File uploaded: {file_path}")

    st.markdown("---")
    st.subheader("⚡ Quick Commands")

    quick_commands = [
        ("Convert file to PDF",              "File to PDF",             "[MODE: File to PDF] Ask the user to upload their file via the sidebar, then convert it to PDF."),
        ("Debug my code",                    "Code Debugging",          "[MODE: Code Debugging] Ask the user to paste or upload their code and describe the issue."),
        ("Write a Salesforce Apex trigger",  "Salesforce Expert",       "[MODE: Salesforce Expert] Ask the user which object the trigger is for and what behaviour they need."),
        ("Create an Instagram Reel script",  "Instagram Reel Script",   "[MODE: Instagram Reel Script] Ask for topic, duration, niche, and tone before writing the script."),
        ("Create a YouTube video script",    "YouTube Script",          "[MODE: YouTube Script] Ask for topic, video length, style, and target audience before writing."),
        ("Resize / edit an image",           "Image Editing",           "[MODE: Image Editing] Ask the user to upload the image and describe what they want done."),
        ("Add watermark to image",           "Image Editing",           "[MODE: Image Editing] Ask the user to upload the image and provide the watermark text."),
        ("Write code for me",                "Code Writing",            "[MODE: Code Writing] Ask the user what language and what they want built."),
        ("Explain Salesforce concepts",      "Salesforce Expert",       "[MODE: Salesforce Expert] Ask which Salesforce topic or concept they want explained."),
        ("🔍 Search the web",                "Web Research",            "[MODE: Web Research] Ask the user what they want thoroughly researched — you will search the live web, forums, and community resources to give a comprehensive, real-time answer."),
        ("🐙 Build & host GitHub app",        "Build GitHub App",        "[MODE: Build GitHub App] Ask for: app name, short description, type (HTML landing page / React app / Python Flask / Node.js), and whether the repo should be public or private. Then build, push, and host it."),
        ("⚡ Autonomous task",               "Autonomous Task",         "[MODE: Autonomous Task] Ask the user to describe ANY task they want you to complete fully and autonomously — no matter how complex or multi-step."),
    ]

    for label, mode_name, intro_prompt in quick_commands:
        if st.button(label, use_container_width=True, key=f"qc_{label[:20]}"):
            st.session_state.active_mode = mode_name
            st.session_state.quick_command = intro_prompt
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True, key="clear_btn"):
        st.session_state.messages = []
        st.session_state.agent.reset_conversation()
        st.session_state.active_mode = None
        st.rerun()

    st.markdown("---")
    st.subheader("🎯 Capabilities")
    st.markdown("""
<div class="cap-list">
  <div class="cap-item">💬 Q&A</div>
  <div class="cap-item">💻 Code</div>
  <div class="cap-item">☁️ Salesforce</div>
  <div class="cap-item">📄 Documents</div>
  <div class="cap-item">🖼️ Images</div>
  <div class="cap-item">📑 → PDF</div>
  <div class="cap-item">🎬 Reels</div>
  <div class="cap-item">▶️ YouTube</div>
  <div class="cap-item">🔍 Web Search</div>
  <div class="cap-item">🐙 GitHub</div>
  <div class="cap-item">⚡ Shell/CLI</div>
  <div class="cap-item">🤖 Auto-tasks</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN CHAT UI
# ─────────────────────────────────────────────

# Logo bar
st.markdown("""
<div class="apex-logo-bar">
  <div class="apex-logo-icon">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 56" width="42" height="42">
      <defs>
        <linearGradient id="aBg" x1="0" y1="0" x2="56" y2="56" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#222"/>
          <stop offset="100%" stop-color="#080808"/>
        </linearGradient>
        <radialGradient id="aSh" cx="38%" cy="22%" r="55%">
          <stop offset="0%" stop-color="#fff" stop-opacity="0.13"/>
          <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
        </radialGradient>
        <filter id="aGl" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="1.2" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <rect width="56" height="56" rx="12" fill="url(#aBg)"/>
      <rect width="56" height="56" rx="12" fill="url(#aSh)"/>
      <rect width="56" height="56" rx="12" fill="none" stroke="#2e2e2e" stroke-width="0.8"/>
      <polyline points="4,12 4,4 12,4" fill="none" stroke="#404040" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <polyline points="44,4 52,4 52,12" fill="none" stroke="#404040" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <polyline points="52,44 52,52 44,52" fill="none" stroke="#404040" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <polyline points="12,52 4,52 4,44" fill="none" stroke="#404040" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="28" y1="10" x2="13" y2="47" stroke="#e0e0e0" stroke-width="3.5" stroke-linecap="round"/>
      <line x1="28" y1="10" x2="43" y2="47" stroke="#e0e0e0" stroke-width="3.5" stroke-linecap="round"/>
      <line x1="19.5" y1="33.5" x2="36.5" y2="33.5" stroke="#e0e0e0" stroke-width="3.5" stroke-linecap="round"/>
      <circle cx="28" cy="10" r="3.5" fill="#ffffff" filter="url(#aGl)"/>
      <circle cx="28" cy="10" r="6.5" fill="none" stroke="#ffffff" stroke-width="0.8" stroke-opacity="0.28"/>
      <circle cx="13" cy="47" r="2.5" fill="#707070"/>
      <circle cx="43" cy="47" r="2.5" fill="#707070"/>
    </svg>
  </div>
  <div class="apex-logo-text"><span>APEX</span> AI Agent</div>
</div>
""", unsafe_allow_html=True)

# Show active mode badge
if st.session_state.get("active_mode"):
    st.markdown(
        f'<div class="file-badge" style="background:rgba(0,0,0,0.07);border-color:#333333;">'
        f'⚡ Mode: <strong>{st.session_state.active_mode}</strong>&nbsp;&nbsp;'
        f'<span style="cursor:pointer;opacity:0.6;font-size:0.8rem;" '
        f'title="Clear mode">✕</span></div>',
        unsafe_allow_html=True
    )

# Show uploaded file badge
if st.session_state.uploaded_file_path:
    fname = Path(st.session_state.uploaded_file_path).name
    st.markdown(f'<div class="file-badge">📎 {fname} ready</div>', unsafe_allow_html=True)

# Welcome card when no messages yet
if not st.session_state.messages:
    st.markdown("""
<div class="welcome-card">
  <div class="big-icon">✨</div>
  <h2>How can I help you today?</h2>
  <p>I can write code, debug, answer questions, convert files to PDF,<br>edit images, create social media scripts, and more.</p>
</div>
""", unsafe_allow_html=True)

    # Functional quick-action chips (2 rows of 3)
    # Each entry: (button label, mode name, intro prompt sent to Claude)
    chip_actions = [
        (
            "💻 Write Code",
            "Code Writing",
            "[MODE: Code Writing] You are now in Code Writing mode. "
            "Greet the user in one short sentence, then ask them: "
            "(1) what programming language, and (2) what they want you to build or write. "
            "Do NOT write any code yet — wait for their answer.",
        ),
        (
            "☁️ Salesforce",
            "Salesforce Expert",
            "[MODE: Salesforce Expert] You are now in Salesforce Expert mode. "
            "Greet the user in one short sentence, then ask them what Salesforce topic "
            "they need help with — e.g. Apex, LWC, SOQL, Flows, integrations, architecture, "
            "certifications, or something else. Do NOT answer anything yet — wait for their input.",
        ),
        (
            "📑 File → PDF",
            "File to PDF",
            "[MODE: File to PDF] You are now in File-to-PDF conversion mode. "
            "Greet the user in one short sentence, then ask them to upload the file they want "
            "to convert (Word, Excel, PowerPoint, image, text, etc.) using the upload button "
            "in the sidebar. Tell them to describe the file if they'd like text-only instructions instead.",
        ),
        (
            "🔍 Search Web",
            "Web Research",
            "[MODE: Web Research] You are now in Deep Web Research mode. "
            "Greet the user in one short sentence, then ask what they would like researched. "
            "You will search the live internet, developer forums (Reddit, Stack Overflow, "
            "Hacker News, GitHub, dev.to), documentation, and news sources — "
            "then synthesise a comprehensive real-time answer. Do NOT answer yet — wait for their topic.",
        ),
        (
            "🐙 GitHub App",
            "Build GitHub App",
            "[MODE: Build GitHub App] You are now in GitHub App Builder mode. "
            "Greet the user in one short sentence, then ask: "
            "(1) App/repo name, "
            "(2) What the app should do (brief description), "
            "(3) Type — HTML+CSS+JS landing page, React SPA, Python Flask, Node.js Express, or other, "
            "(4) Public or private repo? "
            "Once they answer, you will autonomously write all code, create the GitHub repo, "
            "push every file, enable GitHub Pages, and return the live URL. "
            "Do NOT start yet — wait for their answers.",
        ),
        (
            "🎬 Reel Script",
            "Instagram Reel Script",
            "[MODE: Instagram Reel Script] You are now in Instagram Reel Script mode. "
            "Greet the user in one short sentence, then ask them these questions: "
            "(1) What is the topic of the reel? "
            "(2) How long should it be — 15, 30, 60, or 90 seconds? "
            "(3) What niche or industry (tech, business, lifestyle, fitness, etc.)? "
            "(4) What tone — engaging, funny, motivational, or professional? "
            "Do NOT write the script yet — wait for their answers.",
        ),
        (
            "🖼️ Edit Image",
            "Image Editing",
            "[MODE: Image Editing] You are now in Image Editing mode. "
            "Greet the user in one short sentence, then ask them: "
            "(1) Please upload the image using the sidebar upload button. "
            "(2) What would you like to do — resize, convert format, add watermark, "
            "adjust brightness/contrast/saturation, or something else? "
            "Do NOT do anything yet — wait for their upload and instructions.",
        ),
        (
            "🐛 Debug Code",
            "Code Debugging",
            "[MODE: Code Debugging] You are now in Code Debugging mode. "
            "Greet the user in one short sentence, then ask them to either: "
            "(1) paste their code directly in the chat, or "
            "(2) upload the code file using the sidebar upload button. "
            "Also ask what error or issue they are experiencing. "
            "Do NOT debug anything yet — wait for the code.",
        ),
        (
            "⚡ Autonomous Task",
            "Autonomous Task",
            "[MODE: Autonomous Task] You are now in Autonomous Execution mode. "
            "Greet the user in one short sentence. "
            "Ask them to describe ANY task — complex or multi-step — that they want you to "
            "complete entirely on their behalf. You will plan the steps, execute each one "
            "using your tools, and deliver the completed result. Wait for their task description.",
        ),
    ]
    cols1 = st.columns(3)
    cols2 = st.columns(3)
    cols3 = st.columns(3)
    for i, (label, mode_name, intro_prompt) in enumerate(chip_actions):
        if i < 3:
            col = cols1[i]
        elif i < 6:
            col = cols2[i - 3]
        else:
            col = cols3[i - 6]
        with col:
            if st.button(label, use_container_width=True, key=f"chip_{i}"):
                st.session_state.active_mode = mode_name
                st.session_state.quick_command = intro_prompt
                st.rerun()

# Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Resolve prompt: quick command or chat input
if st.session_state.quick_command:
    prompt = st.session_state.quick_command
    st.session_state.quick_command = None
else:
    prompt = st.chat_input("Message APEX...")

# Process user input
if prompt:
    # Clear mode after user replies (mode served its purpose)
    is_mode_intro = prompt.startswith("[MODE:")
    if not is_mode_intro:
        st.session_state.active_mode = None

    # Only show user-visible messages (hide internal mode intro prompts)
    display_prompt = prompt if not is_mode_intro else None
    if display_prompt:
        st.session_state.messages.append({"role": "user", "content": display_prompt})
        with st.chat_message("user"):
            st.markdown(display_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.chat(
                    user_message=prompt,
                    uploaded_file_path=st.session_state.uploaded_file_path,
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                if not is_mode_intro:
                    st.session_state.uploaded_file_path = None  # clear after use
            except Exception as exc:
                error_msg = f"❌ Error: {exc}"
                st.error(error_msg)
                log.error(f"Agent error: {exc}")
