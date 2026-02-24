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
    --primary: #6C63FF;
    --primary-dark: #5a52d5;
    --bg: #0E1117;
    --surface: #1a1d27;
    --surface2: #22263a;
    --border: #2e3250;
    --text: #e8eaf6;
    --text-muted: #8b8fa8;
    --user-bubble: #6C63FF;
    --bot-bubble: #1e2235;
    --radius: 16px;
    --radius-sm: 10px;
}

/* ── Base reset ── */
html, body, [data-testid="stAppViewContainer"] {
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

/* ── App header bar ── */
.apex-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
    background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
    border-radius: var(--radius);
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 24px rgba(108,99,255,0.3);
}
.apex-header .apex-icon { font-size: 2rem; }
.apex-header h1 {
    margin: 0 !important;
    font-size: clamp(1.1rem, 4vw, 1.5rem) !important;
    font-weight: 700 !important;
    color: #fff !important;
    line-height: 1.2 !important;
}
.apex-header p {
    margin: 2px 0 0 0 !important;
    font-size: clamp(0.72rem, 2.5vw, 0.85rem) !important;
    color: rgba(255,255,255,0.8) !important;
}

/* ── Upload indicator badge ── */
.file-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(108,99,255,0.15);
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
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(108,99,255,0.18) 0%, rgba(139,92,246,0.10) 100%) !important;
    border-color: var(--primary) !important;
}
[data-testid="stChatMessage"] p {
    font-size: clamp(0.88rem, 3vw, 1rem) !important;
    line-height: 1.65 !important;
    color: var(--text) !important;
}
[data-testid="stChatMessage"] code {
    font-size: clamp(0.78rem, 2.5vw, 0.88rem) !important;
    background: rgba(108,99,255,0.15) !important;
    border-radius: 5px !important;
    padding: 1px 5px !important;
}
[data-testid="stChatMessage"] pre {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    overflow-x: auto !important;
}

/* ── Chat input bar ── */
[data-testid="stChatInput"] {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 6px 16px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.2) !important;
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
    background: var(--surface) !important;
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
    background: var(--surface2) !important;
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
    background: var(--surface2) !important;
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
    background: var(--surface2);
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
    padding: 2.5rem 1.5rem;
    text-align: center;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin: 1rem 0;
}
.welcome-card .big-icon { font-size: 3.5rem; margin-bottom: 0.8rem; }
.welcome-card h2 {
    font-size: clamp(1rem, 4vw, 1.3rem) !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    margin-bottom: 0.5rem !important;
}
.welcome-card p {
    color: var(--text-muted) !important;
    font-size: clamp(0.82rem, 3vw, 0.92rem) !important;
    max-width: 400px;
}
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-top: 1.2rem;
}
.chip {
    background: rgba(108,99,255,0.12);
    border: 1px solid rgba(108,99,255,0.3);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: clamp(0.72rem, 2.5vw, 0.82rem);
    color: var(--primary);
    cursor: pointer;
    transition: background 0.15s;
}
.chip:hover { background: rgba(108,99,255,0.25); }

/* ── Welcome chip buttons ── */
[data-testid="stMain"] div[data-testid="column"] .stButton > button {
    background: rgba(108,99,255,0.10) !important;
    color: var(--primary) !important;
    border: 1.5px solid rgba(108,99,255,0.35) !important;
    border-radius: 24px !important;
    font-size: clamp(0.75rem, 2.5vw, 0.85rem) !important;
    padding: 10px 8px !important;
    min-height: 44px !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
[data-testid="stMain"] div[data-testid="column"] .stButton > button:hover {
    background: var(--primary) !important;
    color: #fff !important;
    border-color: var(--primary) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(108,99,255,0.35) !important;
}

/* ── Mobile breakpoints ── */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.6rem 0.5rem 5rem 0.5rem !important;
    }
    .apex-header { padding: 12px 14px; gap: 10px; }
    [data-testid="stChatMessage"] { padding: 10px 12px !important; }
    .cap-list { grid-template-columns: 1fr; }
    [data-testid="stSidebar"] { width: 85vw !important; }
}

@media (max-width: 480px) {
    .apex-header { flex-wrap: wrap; }
    .apex-header .apex-icon { font-size: 1.6rem; }
    .chip { font-size: 0.7rem; padding: 4px 10px; }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "agent" not in st.session_state:
    st.session_state.agent = AIAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

if "quick_command" not in st.session_state:
    st.session_state.quick_command = None

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
        "Convert uploaded file to PDF",
        "Debug the uploaded code file",
        "Write a Salesforce Apex trigger for Account",
        "Create a 30-second Instagram Reel script about AI",
        "Create a YouTube video script about Salesforce basics",
        "Resize the uploaded image to 800x600",
        "Add a watermark to the uploaded image",
        "Write a Python function to sort a list of dicts",
        "Explain Salesforce governor limits",
    ]

    for cmd in quick_commands:
        if st.button(cmd, use_container_width=True, key=f"qc_{cmd[:20]}"):
            st.session_state.quick_command = cmd
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True, key="clear_btn"):
        st.session_state.messages = []
        st.session_state.agent.reset_conversation()
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
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN CHAT UI
# ─────────────────────────────────────────────

# Header
st.markdown("""
<div class="apex-header">
  <span class="apex-icon">🤖</span>
  <div>
    <h1>APEX AI Agent</h1>
    <p>Ask anything · Upload files · Write code · Create content</p>
  </div>
</div>
""", unsafe_allow_html=True)

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
    chip_actions = [
        ("💻 Write Code",    "Write a Python function to reverse a string"),
        ("☁️ Salesforce",    "Explain Salesforce governor limits with examples"),
        ("📑 File → PDF",   "How do I convert a Word document to PDF?"),
        ("🎬 Reel Script",  "Create a 30-second Instagram Reel script about AI productivity"),
        ("🖼️ Edit Image",   "How do I resize and add a watermark to an image?"),
        ("🐛 Debug Code",   "Debug the uploaded code file"),
    ]
    cols1 = st.columns(3)
    cols2 = st.columns(3)
    for i, (label, action) in enumerate(chip_actions):
        col = cols1[i] if i < 3 else cols2[i - 3]
        with col:
            if st.button(label, use_container_width=True, key=f"chip_{i}"):
                st.session_state.quick_command = action
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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.chat(
                    user_message=prompt,
                    uploaded_file_path=st.session_state.uploaded_file_path,
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.uploaded_file_path = None  # clear after use
            except Exception as exc:
                error_msg = f"❌ Error: {exc}"
                st.error(error_msg)
                log.error(f"Agent error: {exc}")
