from app.models.document import Document


def build_prompt(
    query: str,
    documents: list[Document],
) -> str:
    """
    Build the prompt sent to the LLM.
    """

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    prompt = f"""
You are Archon AI.

You answer questions ONLY using the provided context.

Rules:
1. Do NOT make up information.
2. If the answer is not in the context, say:
   "I couldn't find that information in the uploaded document."
3. Keep answers concise and accurate.

------------------------
Context
------------------------

{context}

------------------------
Question
------------------------

{query}

------------------------
Answer
------------------------
"""

    return prompt.strip()