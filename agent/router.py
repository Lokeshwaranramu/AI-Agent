"""
Task detection and routing module.
Analyses the user's message and determines which capability to emphasise.
"""
import re
from typing import Literal

TaskType = Literal[
    "code",
    "salesforce",
    "document",
    "image",
    "pdf_conversion",
    "instagram_reel",
    "youtube_video",
    "qa",
]

# Simple keyword-based router
_ROUTES: list[tuple[list[str], TaskType]] = [
    (["apex", "lwc", "soql", "salesforce", "trigger", "batch", "governor", "cpq"], "salesforce"),
    (["instagram", "reel", "tiktok", "short video"], "instagram_reel"),
    (["youtube", "video script", "youtube script", "yt video"], "youtube_video"),
    (["convert to pdf", "image to pdf", "word to pdf", "excel to pdf", "pptx to pdf"], "pdf_conversion"),
    (["modify document", "edit word", "edit excel", "edit docx", "update spreadsheet"], "document"),
    (["resize image", "watermark", "crop image", "convert image", "adjust brightness"], "image"),
    (["write code", "debug", "fix code", "function", "class", "script", "implement"], "code"),
]


def detect_task_type(message: str) -> TaskType:
    """
    Detect the primary task type from the user's message.

    Args:
        message: Raw user message

    Returns:
        One of the TaskType literals
    """
    lower = message.lower()
    for keywords, task in _ROUTES:
        if any(kw in lower for kw in keywords):
            return task
    return "qa"
