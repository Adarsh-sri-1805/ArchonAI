from __future__ import annotations

from typing import List
from app.models.document import Document


def format_document_context(documents: List[Document]) -> str:
    """Format document chunks into structured context blocks with rich source metadata headers."""
    formatted_blocks = []

    for idx, doc in enumerate(documents, start=1):
        meta = doc.metadata or {}
        source = meta.get("file") or meta.get("source") or "Document"
        repo = meta.get("repository")
        if repo and not source.startswith(repo):
            source = f"{repo}/{source}"

        header_parts = [f"Source: {source}"]

        symbol = meta.get("symbol")
        if symbol:
            header_parts.append(f"Symbol: {symbol}")

        start_line = meta.get("start_line")
        end_line = meta.get("end_line")
        if start_line and end_line:
            header_parts.append(f"Lines: {start_line}-{end_line}")

        page = meta.get("page")
        if page:
            header_parts.append(f"Page: {page}")

        header = " | ".join(header_parts)
        block = f"--- [{idx}] {header} ---\n{doc.page_content.strip()}"
        formatted_blocks.append(block)

    return "\n\n".join(formatted_blocks)


def build_prompt(
    query: str,
    documents: List[Document],
) -> str:
    """
    Build an intelligent, analytical prompt for Archon AI using retrieved context.
    """
    context = format_document_context(documents) if documents else "No relevant context found."

    prompt = f"""You are Archon AI, an intelligent codebase and document assistant.

Your task is to provide clear, well-reasoned, and accurate answers to the user's query by analyzing and synthesizing the provided context.

Guidelines:
1. Thorough Analysis & Synthesis: Actively analyze the context snippets, trace code logic across functions and files, and explain how components interact.
2. Grounding & Citations: Base your explanation on the provided context. Refer to relevant file names, line numbers, function/class names, or document pages whenever present in the context headers.
3. Clarity & Depth: Provide actionable, well-structured, and helpful answers. If the context contains partial information, synthesize what is available and explain clearly.

==================================================
CONTEXT & SOURCES
==================================================

{context}

==================================================
USER QUESTION
==================================================

{query}

==================================================
ARCHON AI RESPONSE
==================================================
"""

    return prompt.strip()