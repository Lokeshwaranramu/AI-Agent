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
from tools.code_tools import analyze_code_for_bugs, execute_python_code
from tools.document_tools import modify_excel_file, modify_word_document
from tools.image_tools import add_watermark, adjust_image, convert_image_format, resize_image
from tools.pdf_tools import convert_any_to_pdf
from tools.salesforce_tools import sf_client
from tools.video_tools import create_instagram_reel_script, create_youtube_video_package
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
            api_key=os.getenv("ANTHROPIC_API_KEY"),
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
