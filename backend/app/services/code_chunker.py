import ast

from app.models.document import Document


def chunk_generic_file(
    source: str,
    metadata: dict,
) -> list[Document]:

    return [
        Document(
            page_content=source,
            metadata=metadata,
        )
    ]


def chunk_python_file(
    source: str,
    metadata: dict,
) -> list[Document]:

    try:
        tree = ast.parse(source)
    except Exception:
        return chunk_generic_file(
            source,
            metadata,
        )

    documents = []
    lines = source.splitlines()
    top_level_lines = []

    for node in tree.body:
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", len(lines))

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
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
                        "is_ast": True,
                    },
                )
            )
        else:
            # Collect top-level imports, assignments, module setup
            node_code = "\n".join(lines[start - 1 : end])
            top_level_lines.append(node_code)

    if top_level_lines:
        top_code = "\n".join(top_level_lines).strip()
        if top_code:
            documents.insert(
                0,
                Document(
                    page_content=top_code,
                    metadata={
                        **metadata,
                        "symbol": "module_header",
                        "symbol_type": "ModuleHeader",
                        "start_line": 1,
                        "end_line": len(lines),
                        "is_ast": True,
                    },
                ),
            )

    if not documents:
        return chunk_generic_file(
            source,
            metadata,
        )

    return documents



def chunk_javascript_file(
    source: str,
    metadata: dict,
):
    return chunk_generic_file(
        source,
        metadata,
    )


def chunk_java_file(
    source: str,
    metadata: dict,
):
    return chunk_generic_file(
        source,
        metadata,
    )


def chunk_cpp_file(
    source: str,
    metadata: dict,
):
    return chunk_generic_file(
        source,
        metadata,
    )


def chunk_code(
    source: str,
    extension: str,
    metadata: dict,
):

    extension = extension.lower()

    if extension == ".py":
        return chunk_python_file(
            source,
            metadata,
        )

    if extension in {
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
    }:
        return chunk_javascript_file(
            source,
            metadata,
        )

    if extension == ".java":
        return chunk_java_file(
            source,
            metadata,
        )

    if extension in {
        ".cpp",
        ".c",
        ".hpp",
        ".h",
    }:
        return chunk_cpp_file(
            source,
            metadata,
        )

    return chunk_generic_file(
        source,
        metadata,
    )