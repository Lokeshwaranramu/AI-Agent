"""
Social media content creation tools.
Generates complete scripts for Instagram Reels and YouTube videos.
"""
from typing import Any, Dict

from utils.logger import log


def create_instagram_reel_script(
    topic: str,
    duration_seconds: int = 30,
    niche: str = "general",
    tone: str = "engaging",
    include_hashtags: bool = True,
) -> Dict[str, Any]:
    """
    Generate a complete Instagram Reel script package.

    Args:
        topic: The topic or subject of the reel
        duration_seconds: Target duration (15, 30, 60, or 90 seconds)
        niche: Content niche (tech, business, lifestyle, education, etc.)
        tone: Tone of voice (engaging, professional, funny, motivational)
        include_hashtags: Whether to include hashtag suggestions

    Returns:
        Dict containing: topic, duration, niche, tone, structure, format, instructions
    """
    log.info(f"Generating Instagram Reel script for: {topic}")

    return {
        "topic": topic,
        "duration": duration_seconds,
        "niche": niche,
        "tone": tone,
        "include_hashtags": include_hashtags,
        "structure": {
            "hook": f"First 3 seconds — attention-grabbing hook about {topic}",
            "intro": "Seconds 4-8 — introduce the value of this video",
            "main_content": f"Seconds 9-{duration_seconds - 8} — core content about {topic}",
            "cta": "Last 5 seconds — call to action",
        },
        "format": "vertical 9:16",
        "recommended_music": "Trending audio from Instagram Reels library",
        "instructions": (
            f"Generate a complete {duration_seconds}-second {tone} Instagram Reel script "
            f"about '{topic}' for a {niche} audience. Include:\n"
            "1. Hook line (first 3 seconds)\n"
            "2. Full voiceover script with timestamps\n"
            "3. Text overlay suggestions for each segment\n"
            "4. Visual / B-roll ideas for each segment\n"
            "5. Instagram caption (150–200 words)\n"
            f"{'6. 30 relevant hashtags' if include_hashtags else ''}"
        ),
    }


def create_youtube_video_package(
    topic: str,
    video_length_minutes: int = 10,
    video_style: str = "tutorial",
    target_audience: str = "general",
    channel_niche: str = "technology",
) -> Dict[str, Any]:
    """
    Generate a complete YouTube video content package.

    Args:
        topic: Video topic
        video_length_minutes: Target video length
        video_style: Style (tutorial, vlog, review, explainer, storytime)
        target_audience: Target viewer demographic
        channel_niche: Channel's main niche

    Returns:
        Dict containing metadata and instructions for full content generation
    """
    log.info(f"Generating YouTube video package for: {topic}")

    return {
        "topic": topic,
        "length_minutes": video_length_minutes,
        "style": video_style,
        "audience": target_audience,
        "niche": channel_niche,
        "deliverables": [
            "5 SEO-optimized title options",
            "Full video description with keywords",
            f"Complete {video_length_minutes}-minute script with timestamps",
            "Chapter markers with timestamps",
            "30 SEO tags",
            "3 thumbnail concept descriptions",
            "End screen suggestions",
            "Pinned comment template",
        ],
        "instructions": (
            f"Generate a complete YouTube video package for a {video_length_minutes}-minute "
            f"{video_style} about '{topic}' targeting {target_audience} "
            f"in the {channel_niche} niche. "
            "Provide all deliverables listed above in full detail."
        ),
    }
