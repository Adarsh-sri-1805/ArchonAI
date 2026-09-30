from __future__ import annotations

import ast
import logging
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.config import settings
from src.domain.schemas import Document
from src.core.logger import logger


class ChunkService:
    """
    ChunkService handles splitting documents into semantic chunks.
    It combines AST-based code segment chunking (for Python files) and
    recursive character text splitting (for generic files and long segments).
    """

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        self._chunk_size = chunk_size or settings.CHUNK_SIZE
        self._chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of transient documents into smaller overlapping chunks
        using RecursiveCharacterTextSplitter, while preserving and updating chunk metadata.
        """
        chunks = []
        for document in documents:
            split_texts = self._text_splitter.split_text(document.page_content)
            for chunk_number, text in enumerate(split_texts, start=1):
                metadata = document.metadata.copy()
                metadata["chunk"] = chunk_number
                chunks.append(
                    Document(page_content=text, metadata=metadata)
                )
        return chunks

    def chunk_code_file(self, source: str, extension: str, metadata: dict) -> List[Document]:
        """
        Applies code symbol parsing (e.g. AST parsing for Python) to split a code
        file into symbol-level documents (functions, classes, async functions).
        For unsupported languages, falls back to whole-file generic documents.
        """
        ext = extension.lower()
        if ext == ".py":
            return self._chunk_python_file(source, metadata)
        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            return self._chunk_generic_file(source, metadata)  # Placeholder/legacy parity
        elif ext == ".java":
            return self._chunk_generic_file(source, metadata)  # Placeholder/legacy parity
        elif ext in {".cpp", ".c", ".hpp", ".h"}:
            return self._chunk_generic_file(source, metadata)  # Placeholder/legacy parity
        return self._chunk_generic_file(source, metadata)

    # ── Internal Python AST parsing chunker ────────────────────────────────────

    def _chunk_generic_file(self, source: str, metadata: dict) -> List[Document]:
        return [
            Document(page_content=source, metadata=metadata)
        ]

    def _chunk_python_file(self, source: str, metadata: dict) -> List[Document]:
        try:
            tree = ast.parse(source)
        except Exception as e:
            logger.warning("AST parse failed, falling back to generic chunking: %s", e)
            return self._chunk_generic_file(source, metadata)

        documents = []
        lines = source.splitlines()

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue

            start = node.lineno
            end = node.end_lineno

            code = "\n".join(lines[start - 1 : end])

            documents.append(
                Document(
                    page_content=code,
                    metadata={
                        **metadata,
                        "symbol": node.name,
                        "symbol_type": type(node).__name__,
                        "start_line": start,
                        "end_line": end,
                    }
                )
            )

        if not documents:
            return self._chunk_generic_file(source, metadata)

        return documents
