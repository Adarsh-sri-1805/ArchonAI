from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd
from docx import Document

from app.models.document import Document as ArchonDocument


def parse_document(file_path: str | Path) -> list[ArchonDocument]:
    """
    Detect the file type and return a list of Documents.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _parse_pdf(file_path)

    elif suffix == ".csv":
        return _parse_csv(file_path)

    elif suffix == ".docx":
        return _parse_docx(file_path)

    elif suffix == ".txt":
        return _parse_txt(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")


def _parse_pdf(file_path: Path) -> list[ArchonDocument]:
    documents = []

    with fitz.open(file_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            documents.append(
                ArchonDocument(
                    page_content=page.get_text(),
                    metadata={
                        "source": file_path.name,
                        "page": page_number,
                        "type": "pdf"
                    }
                )
            )

    return documents


def _parse_csv(file_path: Path) -> list[ArchonDocument]:
    df = pd.read_csv(file_path)

    return [
        ArchonDocument(
            page_content=df.to_string(index=False),
            metadata={
                "source": file_path.name,
                "type": "csv"
            }
        )
    ]


def _parse_docx(file_path: Path) -> list[ArchonDocument]:
    doc = Document(file_path)

    return [
        ArchonDocument(
            page_content="\n".join(
                paragraph.text
                for paragraph in doc.paragraphs
            ),
            metadata={
                "source": file_path.name,
                "type": "docx"
            }
        )
    ]


def _parse_txt(file_path: Path) -> list[ArchonDocument]:
    with open(file_path, "r", encoding="utf-8") as file:
        return [
            ArchonDocument(
                page_content=file.read(),
                metadata={
                    "source": file_path.name,
                    "type": "txt"
                }
            )
        ]