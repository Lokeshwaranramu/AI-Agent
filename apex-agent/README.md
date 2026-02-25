# APEX — Autonomous Personal EXecutive Agent

<div align="center">

**APEX**

*Elite, fully autonomous AI agent powered by Ollama*

![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?style=flat-square&logo=typescript)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-4-38bdf8?style=flat-square&logo=tailwindcss)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-white?style=flat-square)

</div>

---

## What is APEX?

APEX is a full-stack AI agent with a sleek web interface that runs **entirely locally** via Ollama. It can execute code, search the web, generate images, create videos, manage files, automate browsers, analyze data, and more — all through natural conversation.

### 10 Capability Areas

| # | Capability | Tools |
|---|---|---|
| 1 | **Code Execution** | Python, JavaScript, Bash, shell commands |
| 2 | **Web Search** | DuckDuckGo search, URL fetching |
| 3 | **Image Generation** | Pollinations.ai (free, no API key) |
| 4 | **Video Creation** | FFmpeg-based video editing |
| 5 | **File Management** | Read, write, list files and directories |
| 6 | **Browser Automation** | Navigate, click, type, screenshot, scrape |
| 7 | **Data Analytics** | Pandas, NumPy, Matplotlib, Seaborn |
| 8 | **Content Creation** | Blog posts, social media, docs, READMEs |
| 9 | **ML Inference** | Hugging Face free inference API |
| 10 | **DevOps** | Docker, Git, CI/CD, deployment |

## Architecture

```
Frontend (Next.js + React + Tailwind CSS)
    │
    │ SSE Stream
    ▼
API Routes (Next.js) ─── Agent Loop ─── Tool Executor
    │
    ├──► Ollama (Local LLM)
    └──► Tool Modules (10 categories)
```

## Prerequisites

1. **Node.js** >= 20.9.0
2. **Ollama** — Install from https://ollama.com
3. **Python 3** (for code execution & data analytics tools)
4. **FFmpeg** (optional, for video creation): `brew install ffmpeg`

## Quick Start

### 1. Install Ollama and pull a model

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama
ollama serve

# Pull a model with tool-calling support
ollama pull llama3.1:8b
```

### 2. Install dependencies and run

```bash
cd apex-agent
npm install
npm run dev
```

### 3. Open the app

Navigate to http://localhost:3000

## Configuration

Edit `.env.local` to customize:

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
HF_TOKEN=your_free_token_here
MAX_TOOL_CALLS=10
TEMPERATURE=0.7
```

### Recommended Models

| Model | Size | Best For |
|---|---|---|
| `llama3.1:8b` | 4.7 GB | General purpose, good tool calling |
| `qwen2.5:7b` | 4.4 GB | Good tool calling, fast |
| `mistral:7b` | 4.1 GB | Fast, decent tool support |
| `command-r:35b` | 20 GB | Excellent tool calling |

## Project Structure

```
apex-agent/
├── src/
│   ├── app/
│   │   ├── api/chat/route.ts       # Main chat SSE endpoint
│   │   ├── api/status/route.ts     # Ollama status check
│   │   ├── layout.tsx / page.tsx   # Root layout & main page
│   │   └── globals.css             # Global styles
│   ├── components/
│   │   ├── ChatInterface.tsx       # Chat input & message flow
│   │   ├── MessageBubble.tsx       # Message rendering (Markdown)
│   │   ├── ToolOutput.tsx          # Tool call/result display
│   │   └── Sidebar.tsx             # Side panel with status
│   ├── config/
│   │   ├── system-prompt.ts        # APEX personality & config
│   │   └── tool-definitions.ts     # All tool schemas
│   ├── lib/
│   │   ├── agent.ts                # Core agent loop
│   │   ├── ollama.ts               # Ollama API client
│   │   ├── tool-executor.ts        # Tool routing & execution
│   │   └── types.ts                # TypeScript definitions
│   └── tools/                      # 10 tool modules
│       ├── code-execution.ts
│       ├── web-search.ts
│       ├── image-generation.ts
│       ├── video-creation.ts
│       ├── file-management.ts
│       ├── browser-automation.ts
│       ├── data-analytics.ts
│       ├── content-creation.ts
│       ├── ml-tools.ts
│       └── devops-tools.ts
└── .env.local
```

## How It Works

1. You type a message in the chat interface
2. The Agent Loop sends your message + tool definitions to Ollama
3. Ollama decides whether to respond with text or call tools
4. If tools are called, the Tool Executor runs them and feeds results back
5. The loop continues until Ollama gives a final text response
6. Everything streams back to the UI in real-time via SSE

## Free Tool Stack

Everything APEX uses is 100% free:

- **LLM**: Ollama (local, unlimited)
- **Web Search**: DuckDuckGo (no API key)
- **Image Gen**: Pollinations.ai (free, no API key)
- **Code Execution**: Local Python/Node.js/Bash
- **ML Inference**: Hugging Face (free tier)
- **Video**: FFmpeg (open source)
- **Browser**: Playwright (open source, optional)

## License

MIT

---

*APEX — Built to execute. Built for one.*
