from __future__ import annotations

import ast
import re
import logging
from typing import List, Dict, Any

from src.domain.schemas import Document
from src.core.logger import logger


class MetadataService:
    """
    MetadataService normalizes and enriches chunk metadata.
    Responsible for ensuring consistent schemas and extracting language-specific
    features (such as imports for Python code) without performing any indexing
    or retrieval operations.
    """

    def enrich_metadata(self, chunk: Document) -> Dict[str, Any]:
        """
        Enriches and normalizes the metadata of a document chunk.
        Fills in default keys (file, repository, language, symbols, line ranges)
        and extracts imports for Python code segments.
        """
        metadata = chunk.metadata.copy()

        # Normalize standard fields
        metadata.setdefault("language", "unknown")
        metadata.setdefault("file", "")
        metadata.setdefault("repository", "")
        metadata.setdefault("symbol", None)
        metadata.setdefault("symbol_type", None)
        metadata.setdefault("start_line", None)
        metadata.setdefault("end_line", None)

        # Language-specific extraction (Python imports)
        if metadata.get("language") == "python":
            if "imports" not in metadata or not metadata["imports"]:
                metadata["imports"] = self._extract_python_imports(chunk.page_content)
        else:
            metadata.setdefault("imports", [])

        return metadata

    def _extract_python_imports(self, code: str) -> List[str]:
        """
        Tries parsing the code segment to extract module import strings.
        """
        try:
            tree = ast.parse(code)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            return list(set(imports))
        except Exception:
            # Fallback to simple regex scan for syntax/AST errors in code segments
            imports = []
            for line in code.splitlines():
                line = line.strip()
                # matches: "import x", "from y import z"
                match = re.match(r"^(?:from|import)\s+([\w\.]+)", line)
                if match:
                    imports.append(match.group(1))
            return list(set(imports))
