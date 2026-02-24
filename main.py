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
    initial_sidebar_state="expanded",
)

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
    st.title("🤖 APEX Agent")
    st.caption("Multi-Capability AI Agent powered by Claude")

    st.markdown("---")
    st.subheader("📁 File Upload")
    uploaded_file = st.file_uploader(
        "Upload a file to work with",
        type=[
            "pdf", "docx", "xlsx", "pptx", "txt", "md", "csv",
            "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp",
            "html", "py", "js", "ts", "java", "cs", "cpp", "go", "rs",
        ],
    )

    if uploaded_file:
        file_path = f"uploads/{uploaded_file.name}"
        with open(file_path, "wb") as fh:
            fh.write(uploaded_file.getbuffer())
        st.session_state.uploaded_file_path = file_path
        st.success(f"✅ {uploaded_file.name} uploaded")
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
        "What is 2 + 2?",
    ]

    for cmd in quick_commands:
        if st.button(cmd, use_container_width=True):
            st.session_state.quick_command = cmd

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent.reset_conversation()
        st.rerun()

    st.markdown("---")
    st.subheader("🎯 Capabilities")
    for cap in [
        "💬 Q&A on any topic",
        "💻 Code in any language",
        "☁️ Salesforce expert",
        "📄 Document modification",
        "🖼️ Image editing",
        "📑 Any file → PDF",
        "🎬 Instagram Reels",
        "▶️ YouTube videos",
        "🐛 Code debugging",
    ]:
        st.markdown(f"• {cap}")

# ─────────────────────────────────────────────
# MAIN CHAT UI
# ─────────────────────────────────────────────

st.title("🤖 APEX — Multi-Capability AI Agent")
st.caption("Ask me anything, upload files, write code, create content, and more.")

# Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Resolve prompt: quick command or chat input
if st.session_state.quick_command:
    prompt = st.session_state.quick_command
    st.session_state.quick_command = None
else:
    prompt = st.chat_input("Ask APEX anything...")

# Process user input
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("APEX is thinking..."):
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
