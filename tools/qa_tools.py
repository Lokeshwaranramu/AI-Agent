"""
Q&A and research tools.
Provides structured prompt templates for answering questions and researching topics.
"""
from utils.logger import log


def build_qa_prompt(question: str, context: str = "") -> str:
    """
    Build a structured Q&A prompt for Claude to answer a question.

    Args:
        question: The user's question
        context: Additional context (e.g., uploaded document content)

    Returns:
        Formatted prompt string
    """
    log.info(f"Building Q&A prompt for: {question[:80]}")

    prompt = f"Answer the following question with expert-level depth and clarity.\n\nQuestion: {question}"
    if context:
        prompt += f"\n\nAdditional Context:\n{context}"
    prompt += (
        "\n\nProvide:\n"
        "1. A clear, direct answer\n"
        "2. Supporting explanation with examples\n"
        "3. Any important caveats or edge cases\n"
        "4. Recommended next steps or resources if applicable"
    )
    return prompt


def build_comparison_prompt(item_a: str, item_b: str, criteria: str = "") -> str:
    """
    Build a structured comparison prompt.

    Args:
        item_a: First item to compare
        item_b: Second item to compare
        criteria: Optional specific criteria to compare on

    Returns:
        Formatted comparison prompt
    """
    prompt = f"Provide a thorough comparison between **{item_a}** and **{item_b}**."
    if criteria:
        prompt += f"\n\nFocus on these criteria: {criteria}"
    prompt += (
        "\n\nStructure your response as:\n"
        "1. Overview of each\n"
        "2. Head-to-head comparison table\n"
        "3. Pros and cons of each\n"
        "4. Best use cases for each\n"
        "5. Final recommendation"
    )
    return prompt
