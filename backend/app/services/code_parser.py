import os
from pathlib import Path

from app.models.document import Document
from app.services.code_chunker import chunk_code


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".sql",
    ".sh",
}


LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".txt": "text",
    ".sql": "sql",
    ".sh": "shell",
}


IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "target",
    ".pytest_cache",
    ".mypy_cache",
    ".next",
    ".nuxt",
    "coverage",
    ".turbo",
    "vendor",
    "bin",
    "obj",
    ".tox",
    ".cache",
    "site-packages",
    "out",
    ".gradle",
}


IGNORED_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "composer.lock",
    "go.sum",
}

MAX_FILE_SIZE_BYTES = 300 * 1024  # 300 KB limit for source code files


def parse_repository(
    repo_path: Path,
) -> list[Document]:
    """
    Parse a repository into semantic code chunks with high-performance
    directory pruning and safety limits.
    """
    documents: list[Document] = []
    repository_name = repo_path.name

    # Use os.walk with directory pruning to avoid traversing ignored folders
    for root, dirs, files in os.walk(repo_path):
        # Prune ignored directories in-place so os.walk does not descend into them
        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRECTORIES and not d.startswith(".")
        ]

        for file_name in files:
            if file_name in IGNORED_FILES or file_name.startswith("."):
                continue

            file_path = Path(root) / file_name
            extension = file_path.suffix.lower()

            # Skip unsupported extensions or minified/map bundles
            if extension not in SUPPORTED_EXTENSIONS:
                continue
            if ".min." in file_name or file_name.endswith(".map"):
                continue

            try:
                # Fast size check before reading entire file
                if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue

                source = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

                if not source.strip():
                    continue

                rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")

                metadata = {
                    "repository": repository_name,
                    "file": rel_path,
                    "source": rel_path,
                    "extension": extension,
                    "language": LANGUAGE_MAP.get(
                        extension,
                        "unknown",
                    ),
                    "type": "github",
                }

                chunks = chunk_code(
                    source=source,
                    extension=extension,
                    metadata=metadata,
                )

                documents.extend(chunks)

            except Exception as e:
                # Log and continue so one corrupt/locked file does not halt indexing
                print(f"[Warning] Failed to process {file_path}: {e}")
                continue

    return documents