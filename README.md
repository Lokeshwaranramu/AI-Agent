# 🤖 APEX — Multi-Capability AI Agent

A fully functional AI agent powered by **Claude (claude-sonnet-4-6)** with a Streamlit web UI.

## Capabilities

| Capability | Description |
|---|---|
| 💬 Q&A | Expert-level answers on any topic |
| 💻 Code | Write, debug, and refactor code in any language |
| ☁️ Salesforce | Apex, LWC, SOQL, integrations, architecture |
| 📄 Documents | Modify Word, Excel, PowerPoint files |
| 🖼️ Images | Resize, convert, watermark, adjust images |
| 📑 PDF Conversion | Convert any file type to PDF |
| 🎬 Instagram Reels | Complete reel scripts with hooks, captions, hashtags |
| ▶️ YouTube Videos | Full video packages with scripts, SEO, thumbnails |

---

## Quick Start

### 1. Clone and set up

```bash
git clone <your-repo-url>
cd ai-agent
python -m venv venv

# Activate venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\Activate.ps1       # Windows PowerShell

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and replace `sk-ant-your-key-here` with your actual Anthropic API key from
[console.anthropic.com](https://console.anthropic.com).

### 3. (Optional) Install LibreOffice for Office → PDF conversion

```bash
# Ubuntu / Debian
sudo apt install libreoffice -y

# macOS
brew install --cask libreoffice

# Windows — download from https://www.libreoffice.org/
```

### 4. Run the agent

```bash
streamlit run main.py
```

Open **http://localhost:8501** in your browser.

---

## Project Structure

```
ai-agent/
├── .github/
│   └── copilot-instructions.md
├── agent/
│   ├── __init__.py
│   ├── core.py           ← Main agent brain (Claude API + tool loop)
│   ├── router.py         ← Task detection
│   └── system_prompt.py  ← Master system prompt
├── tools/
│   ├── __init__.py
│   ├── code_tools.py
│   ├── document_tools.py
│   ├── image_tools.py
│   ├── pdf_tools.py
│   ├── qa_tools.py
│   ├── salesforce_tools.py
│   └── video_tools.py
├── utils/
│   ├── __init__.py
│   ├── file_handler.py
│   ├── logger.py
│   └── validators.py
├── tests/
│   └── __init__.py
├── uploads/              ← Temp upload folder (gitignored)
├── outputs/              ← Generated files (gitignored)
├── logs/                 ← Log files (gitignored)
├── .env                  ← Your secrets (never commit)
├── .env.example          ← Safe to share
├── .gitignore
├── requirements.txt
└── main.py               ← Streamlit entry point
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Claude API key from console.anthropic.com |
| `SF_USERNAME` | Optional | Salesforce username |
| `SF_PASSWORD` | Optional | Salesforce password |
| `SF_SECURITY_TOKEN` | Optional | Salesforce security token |
| `SF_DOMAIN` | Optional | `login` (production) or `test` (sandbox) |
| `LOG_LEVEL` | Optional | `INFO` (default) or `DEBUG` |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'anthropic'`
Virtual environment is not active:
```bash
venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### `AuthenticationError: Invalid API key`
Check `.env` — no spaces around `=`, no quotes, key starts with `sk-ant-`.

### PowerShell execution policy error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port 8501 already in use
```bash
streamlit run main.py --server.port 8502
```

---

## Daily Use

```bash
# Every session
cd ai-agent
venv\Scripts\Activate.ps1   # Windows
streamlit run main.py

# Stop
Ctrl+C
```
