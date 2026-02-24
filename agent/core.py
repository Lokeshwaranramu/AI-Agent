"""
Core agent brain — manages Claude API interaction, tool calling, and response handling.
This is the central orchestrator of the entire agent.
"""
import json
import os
import sys
import warnings
from typing import Any, Dict, List, Optional

import anthropic
import httpx

from agent.system_prompt import MASTER_SYSTEM_PROMPT


def _get_api_key() -> str:
    """
    Retrieve the Anthropic API key.
    Priority: environment variable → Streamlit secrets → raise clear error.
    """
    # 1. Standard env var (works locally with .env and on most cloud platforms)
    key = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
    if key:
        return key

    # 2. Streamlit Cloud secrets (st.secrets acts like a dict)
    try:
        import streamlit as st
        key = str(st.secrets.get("ANTHROPIC_API_KEY", "")).strip().strip('"').strip("'")
        if key:
            return key
    except Exception:
        pass

    raise ValueError(
        "ANTHROPIC_API_KEY is not set. "
        "Add it in Streamlit Cloud → App settings → Secrets as:\n"
        'ANTHROPIC_API_KEY = "sk-ant-api03-..."'
    )
from tools.code_tools import analyze_code_for_bugs, execute_python_code
from tools.document_tools import modify_excel_file, modify_word_document
from tools.image_tools import add_watermark, adjust_image, convert_image_format, resize_image
from tools.pdf_tools import convert_any_to_pdf
from tools.salesforce_tools import sf_client
from tools.video_tools import create_instagram_reel_script, create_youtube_video_package
from tools.web_search_tools import deep_research, fetch_url, forum_search, web_search
from tools.github_tools import (
    create_repository, push_files, enable_github_pages, get_repository,
    list_repositories, create_release, read_file_from_repo, get_github_user, create_workflow,
)
from tools.shell_tools import (
    run_command, write_file, read_file as shell_read_file,
    list_directory, system_info, git_init_and_push, git_clone,
)
from utils.logger import log

# ─────────────────────────────────────────────
# TOOL DEFINITIONS (passed to Claude API)
# ─────────────────────────────────────────────

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "convert_to_pdf",
        "description": (
            "Convert any file (docx, xlsx, pptx, txt, md, csv, html, "
            "jpg, png, gif, bmp, tiff, webp) to PDF format."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the file to convert"},
                "output_path": {"type": "string", "description": "Optional output PDF path"},
            },
            "required": ["input_path"],
        },
    },
    {
        "name": "modify_document",
        "description": (
            "Modify a Word (.docx) or Excel (.xlsx) document. "
            "Supports find/replace text and cell updates."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the document"},
                "document_type": {
                    "type": "string",
                    "enum": ["word", "excel"],
                    "description": "Type of document",
                },
                "replacements": {
                    "type": "object",
                    "description": "For Word: {old_text: new_text} dict",
                },
                "cell_updates": {
                    "type": "object",
                    "description": "For Excel: {cell_address: value} dict",
                },
                "sheet_name": {"type": "string", "description": "Excel sheet name (optional)"},
                "output_path": {
                    "type": "string",
                    "description": "Output path (modifies in place if omitted)",
                },
            },
            "required": ["input_path", "document_type"],
        },
    },
    {
        "name": "modify_image",
        "description": (
            "Modify an image: resize, convert format, add watermark, "
            "or adjust brightness/contrast/saturation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the image"},
                "operation": {
                    "type": "string",
                    "enum": ["resize", "convert_format", "add_watermark", "adjust"],
                    "description": "Operation to perform",
                },
                "width": {"type": "integer", "description": "For resize: target width"},
                "height": {"type": "integer", "description": "For resize: target height"},
                "target_format": {
                    "type": "string",
                    "description": "For convert_format: PNG, JPEG, WEBP, BMP",
                },
                "watermark_text": {
                    "type": "string",
                    "description": "For add_watermark: text to use",
                },
                "brightness": {"type": "number", "description": "For adjust: 1.0 = original"},
                "contrast": {"type": "number", "description": "For adjust: 1.0 = original"},
                "saturation": {"type": "number", "description": "For adjust: 1.0 = original"},
                "output_path": {
                    "type": "string",
                    "description": "Output path (auto-generated if omitted)",
                },
            },
            "required": ["input_path", "operation"],
        },
    },
    {
        "name": "execute_code",
        "description": "Execute Python code safely in a sandbox and return the output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Max execution time (default 30)",
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "salesforce_query",
        "description": "Execute a SOQL query against Salesforce and return results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "soql": {"type": "string", "description": "Valid SOQL query string"},
            },
            "required": ["soql"],
        },
    },
    {
        "name": "create_video_content",
        "description": "Generate a complete content package for Instagram Reels or YouTube videos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["instagram_reel", "youtube"],
                    "description": "Target platform",
                },
                "topic": {"type": "string", "description": "Video topic"},
                "duration_seconds": {
                    "type": "integer",
                    "description": "For Instagram: target duration",
                },
                "video_length_minutes": {
                    "type": "integer",
                    "description": "For YouTube: video length",
                },
                "niche": {"type": "string", "description": "Content niche"},
                "tone": {"type": "string", "description": "Tone of voice"},
            },
            "required": ["platform", "topic"],
        },
    },
    # ─── WEB SEARCH TOOLS ────────────────────────────────────────────────────
    {
        "name": "web_search",
        "description": (
            "Search the live web for any query. Uses Tavily (if API key set) or DuckDuckGo. "
            "Always call this for questions needing current data, documentation, tutorials, "
            "error solutions, pricing, or any real-world facts. Do NOT rely on training data alone."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results (default 10)"},
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "Search depth for Tavily (default 'advanced')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "forum_search",
        "description": (
            "Search specifically in developer forums and communities: Reddit, Stack Overflow, "
            "Hacker News, dev.to, GitHub, Medium, hashnode. Use for bugs, how-to questions, "
            "comparisons, opinions, and community knowledge."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results (default 10)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "deep_research",
        "description": (
            "Run comprehensive multi-query research on a topic. Executes 5 sub-queries "
            "(general, tutorial, best-practices, problems, community) and synthesises all results. "
            "Use when the user wants thorough coverage of a topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Research topic"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "fetch_url",
        "description": "Fetch and return the text content of any URL (web page, API, documentation).",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "max_chars": {"type": "integer", "description": "Max characters to return (default 6000)"},
            },
            "required": ["url"],
        },
    },
    # ─── GITHUB AUTOMATION TOOLS ─────────────────────────────────────────────
    {
        "name": "github_operation",
        "description": (
            "Perform GitHub operations: create repos, push files, enable Pages, "
            "list/get repos, read files from repos, create releases. "
            "Use this to autonomously build and host web applications on GitHub."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "create_repo", "push_files", "enable_pages",
                        "list_repos", "get_repo", "get_user",
                        "create_release", "read_file", "create_workflow",
                    ],
                    "description": "The GitHub action to perform",
                },
                "repo_name": {"type": "string", "description": "Repository name"},
                "description": {"type": "string", "description": "For create_repo: description"},
                "private": {"type": "boolean", "description": "For create_repo: private repo?"},
                "auto_init": {"type": "boolean", "description": "For create_repo: initialize with README?"},
                "gitignore_template": {"type": "string", "description": "e.g. 'Python', 'Node'"},
                "homepage": {"type": "string", "description": "For create_repo: homepage URL"},
                "files": {
                    "type": "object",
                    "description": "For push_files: {\"path/file.ext\": \"content\"} dict",
                },
                "commit_message": {"type": "string", "description": "For push_files: commit message"},
                "branch": {"type": "string", "description": "Target branch (default 'main')"},
                "create_branch": {"type": "boolean", "description": "Create branch if missing?"},
                "pages_path": {"type": "string", "description": "For enable_pages: '/' or '/docs'"},
                "file_path": {"type": "string", "description": "For read_file: path in repo"},
                "tag": {"type": "string", "description": "For create_release: tag name"},
                "release_title": {"type": "string", "description": "For create_release: title"},
                "release_body": {"type": "string", "description": "For create_release: release notes"},
                "workflow_name": {"type": "string", "description": "For create_workflow: filename"},
                "workflow_yaml": {"type": "string", "description": "For create_workflow: YAML content"},
                "limit": {"type": "integer", "description": "For list_repos: max repos to return"},
            },
            "required": ["action"],
        },
    },
    # ─── SHELL / SYSTEM TOOLS ─────────────────────────────────────────────────
    {
        "name": "shell_execute",
        "description": (
            "Execute shell commands and file operations on the local system. "
            "Run git, npm, pip, python, node, curl, make, docker, and any other CLI tool. "
            "Also write/read files and list directories. "
            "Use for scaffolding projects, installing dependencies, building apps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "run_command", "write_file", "read_file",
                        "list_directory", "system_info", "git_push", "git_clone",
                    ],
                    "description": "Action to perform",
                },
                "command": {"type": "string", "description": "For run_command / git_push: shell command or commit message"},
                "working_directory": {"type": "string", "description": "Working directory path"},
                "timeout_seconds": {"type": "integer", "description": "Timeout (default 120)"},
                "file_path": {"type": "string", "description": "For write_file/read_file: file path"},
                "content": {"type": "string", "description": "For write_file: file content"},
                "path": {"type": "string", "description": "For list_directory: directory path"},
                "remote_url": {"type": "string", "description": "For git_push: remote URL"},
                "local_dir": {"type": "string", "description": "For git_push/git_clone: local directory"},
                "branch": {"type": "string", "description": "For git_push: branch name"},
                "repo_url": {"type": "string", "description": "For git_clone: repo URL"},
            },
            "required": ["action"],
        },
    },
]


# ─────────────────────────────────────────────
# TOOL EXECUTOR
# ─────────────────────────────────────────────


def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """
    Execute a tool by name with provided inputs.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Tool input parameters

    Returns:
        String result of the tool execution
    """
    log.info(f"Executing tool: {tool_name} with inputs: {list(tool_input.keys())}")

    try:
        if tool_name == "convert_to_pdf":
            result = convert_any_to_pdf(
                input_path=tool_input["input_path"],
                output_path=tool_input.get("output_path"),
            )
            return f"✅ Successfully converted to PDF: {result}"

        elif tool_name == "modify_document":
            doc_type = tool_input["document_type"]
            if doc_type == "word":
                result = modify_word_document(
                    input_path=tool_input["input_path"],
                    replacements=tool_input.get("replacements", {}),
                    output_path=tool_input.get("output_path"),
                )
                return f"✅ Word document modified: {result}"
            elif doc_type == "excel":
                result = modify_excel_file(
                    input_path=tool_input["input_path"],
                    cell_updates=tool_input.get("cell_updates", {}),
                    sheet_name=tool_input.get("sheet_name"),
                    output_path=tool_input.get("output_path"),
                )
                return f"✅ Excel file modified: {result}"

        elif tool_name == "modify_image":
            op = tool_input["operation"]
            input_path = tool_input["input_path"]
            output_path = tool_input.get("output_path")

            if op == "resize":
                result = resize_image(
                    input_path, tool_input["width"], tool_input["height"], output_path
                )
            elif op == "convert_format":
                result = convert_image_format(input_path, tool_input["target_format"], output_path)
            elif op == "add_watermark":
                result = add_watermark(input_path, tool_input["watermark_text"], output_path)
            elif op == "adjust":
                result = adjust_image(
                    input_path,
                    brightness=tool_input.get("brightness", 1.0),
                    contrast=tool_input.get("contrast", 1.0),
                    saturation=tool_input.get("saturation", 1.0),
                    output_path=output_path,
                )
            else:
                return f"❌ Unknown image operation: {op}"
            return f"✅ Image modified ({op}): {result}"

        elif tool_name == "execute_code":
            result = execute_python_code(
                code=tool_input["code"],
                timeout_seconds=tool_input.get("timeout_seconds", 30),
            )
            return json.dumps(result, indent=2)

        elif tool_name == "salesforce_query":
            records = sf_client.execute_soql(tool_input["soql"])
            return json.dumps(records, indent=2, default=str)

        elif tool_name == "create_video_content":
            platform = tool_input["platform"]
            if platform == "instagram_reel":
                result = create_instagram_reel_script(
                    topic=tool_input["topic"],
                    duration_seconds=tool_input.get("duration_seconds", 30),
                    niche=tool_input.get("niche", "general"),
                    tone=tool_input.get("tone", "engaging"),
                )
            else:
                result = create_youtube_video_package(
                    topic=tool_input["topic"],
                    video_length_minutes=tool_input.get("video_length_minutes", 10),
                    channel_niche=tool_input.get("niche", "general"),
                )
            return json.dumps(result, indent=2)

        # ─── WEB SEARCH TOOLS ───────────────────────────────────────────────
        elif tool_name == "web_search":
            return web_search(
                query=tool_input["query"],
                num_results=tool_input.get("num_results", 10),
                search_depth=tool_input.get("search_depth", "advanced"),
            )

        elif tool_name == "forum_search":
            return forum_search(
                query=tool_input["query"],
                num_results=tool_input.get("num_results", 10),
            )

        elif tool_name == "deep_research":
            return deep_research(topic=tool_input["topic"])

        elif tool_name == "fetch_url":
            return fetch_url(
                url=tool_input["url"],
                max_chars=tool_input.get("max_chars", 6000),
            )

        # ─── GITHUB TOOLS ────────────────────────────────────────────────────
        elif tool_name == "github_operation":
            action = tool_input["action"]

            if action == "create_repo":
                result = create_repository(
                    name=tool_input["repo_name"],
                    description=tool_input.get("description", ""),
                    private=tool_input.get("private", True),
                    auto_init=tool_input.get("auto_init", True),
                    gitignore_template=tool_input.get("gitignore_template"),
                    homepage=tool_input.get("homepage", ""),
                )
                return json.dumps(result, indent=2)

            elif action == "push_files":
                result = push_files(
                    repo_name=tool_input["repo_name"],
                    files=tool_input["files"],
                    commit_message=tool_input.get("commit_message", "feat: add files via APEX"),
                    branch=tool_input.get("branch", "main"),
                    create_branch=tool_input.get("create_branch", False),
                )
                return json.dumps(result, indent=2)

            elif action == "enable_pages":
                result = enable_github_pages(
                    repo_name=tool_input["repo_name"],
                    branch=tool_input.get("branch", "main"),
                    path=tool_input.get("pages_path", "/"),
                )
                return json.dumps(result, indent=2)

            elif action == "list_repos":
                repos = list_repositories(limit=tool_input.get("limit", 20))
                return json.dumps(repos, indent=2)

            elif action == "get_repo":
                result = get_repository(tool_input["repo_name"])
                return json.dumps(result, indent=2)

            elif action == "get_user":
                result = get_github_user()
                return json.dumps(result, indent=2)

            elif action == "create_release":
                result = create_release(
                    repo_name=tool_input["repo_name"],
                    tag=tool_input["tag"],
                    title=tool_input["release_title"],
                    body=tool_input.get("release_body", ""),
                )
                return json.dumps(result, indent=2)

            elif action == "read_file":
                content = read_file_from_repo(
                    repo_name=tool_input["repo_name"],
                    file_path=tool_input["file_path"],
                    branch=tool_input.get("branch", "main"),
                )
                return content

            elif action == "create_workflow":
                url = create_workflow(
                    repo_name=tool_input["repo_name"],
                    workflow_name=tool_input["workflow_name"],
                    workflow_yaml=tool_input["workflow_yaml"],
                    branch=tool_input.get("branch", "main"),
                )
                return f"✅ Workflow created. Actions URL: {url}"

            else:
                return f"❌ Unknown github_operation action: {action}"

        # ─── SHELL / SYSTEM TOOLS ────────────────────────────────────────────
        elif tool_name == "shell_execute":
            action = tool_input["action"]

            if action == "run_command":
                result = run_command(
                    command=tool_input["command"],
                    working_directory=tool_input.get("working_directory"),
                    timeout_seconds=tool_input.get("timeout_seconds", 120),
                )
                return json.dumps(result, indent=2)

            elif action == "write_file":
                result = write_file(
                    file_path=tool_input["file_path"],
                    content=tool_input["content"],
                    working_directory=tool_input.get("working_directory"),
                )
                return json.dumps(result, indent=2)

            elif action == "read_file":
                return shell_read_file(
                    file_path=tool_input["file_path"],
                    working_directory=tool_input.get("working_directory"),
                )

            elif action == "list_directory":
                return list_directory(
                    path=tool_input.get("path", "."),
                    working_directory=tool_input.get("working_directory"),
                )

            elif action == "system_info":
                return json.dumps(system_info(), indent=2)

            elif action == "git_push":
                result = git_init_and_push(
                    local_dir=tool_input["local_dir"],
                    remote_url=tool_input["remote_url"],
                    commit_message=tool_input.get("command", "initial commit"),
                    branch=tool_input.get("branch", "main"),
                )
                return json.dumps(result, indent=2)

            elif action == "git_clone":
                result = git_clone(
                    repo_url=tool_input["repo_url"],
                    target_dir=tool_input.get("local_dir"),
                )
                return json.dumps(result, indent=2)

            else:
                return f"❌ Unknown shell_execute action: {action}"

        else:
            return f"❌ Unknown tool: {tool_name}"

    except Exception as e:
        log.error(f"Tool execution failed [{tool_name}]: {e}")
        return f"❌ Tool error: {str(e)}"


# ─────────────────────────────────────────────
# MAIN AGENT CLASS
# ─────────────────────────────────────────────


class AIAgent:
    """
    Main AI Agent class that orchestrates Claude API calls and tool execution.
    Implements the full agentic loop with tool use.
    """

    def __init__(self) -> None:
        """Initialize the AI Agent with Anthropic client."""
        self.model = "claude-sonnet-4-6"
        self.max_tokens = 8096
        self.conversation_history: List[Dict[str, Any]] = []
        self.client = anthropic.Anthropic(
            api_key=_get_api_key(),
            http_client=self._build_http_client(),
        )
        log.success("AI Agent initialized")

    @staticmethod
    def _build_http_client() -> httpx.Client:
        """
        Build an httpx client.
        On Windows, SSL verification is disabled to work around broken system cert chains.
        On Linux/macOS (production servers) standard SSL verification is used.
        """
        if sys.platform == "win32":
            warnings.filterwarnings("ignore", message="Unverified HTTPS request")
            log.warning("Windows detected — SSL verification disabled for Anthropic API calls")
            return httpx.Client(verify=False)
        return httpx.Client(verify=True)

    def chat(self, user_message: str, uploaded_file_path: Optional[str] = None) -> str:
        """
        Process a user message and return the agent's response.
        Handles multi-turn conversation with tool use.

        Args:
            user_message: The user's input message
            uploaded_file_path: Optional path to an uploaded file

        Returns:
            Agent's final response string
        """
        user_content = user_message
        if uploaded_file_path:
            user_content += f"\n\n[Uploaded file available at: {uploaded_file_path}]"

        self.conversation_history.append({"role": "user", "content": user_content})
        log.info(f"Processing: {user_message[:100]}...")

        # Agentic loop — keeps running until Claude stops using tools
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=MASTER_SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.conversation_history,
            )

            log.debug(f"Claude stop reason: {response.stop_reason}")

            if response.stop_reason == "tool_use":
                # Add Claude's response to history
                self.conversation_history.append(
                    {"role": "assistant", "content": response.content}
                )

                # Execute all requested tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        log.info(f"Tool called: {block.name}")
                        result = execute_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            }
                        )

                self.conversation_history.append(
                    {"role": "user", "content": tool_results}
                )

            elif response.stop_reason == "end_turn":
                final_response = "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                self.conversation_history.append(
                    {"role": "assistant", "content": final_response}
                )
                log.success("Agent response complete")
                return final_response

            else:
                log.warning(f"Unexpected stop reason: {response.stop_reason}")
                return "An unexpected error occurred. Please try again."

    def reset_conversation(self) -> None:
        """Clear conversation history to start a fresh session."""
        self.conversation_history = []
        log.info("Conversation history cleared")
