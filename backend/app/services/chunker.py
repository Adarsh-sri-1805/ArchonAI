from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.models.document import Document


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)


def chunk_documents(documents: list[Document]) -> list[Document]:
    """
    Split documents into overlapping chunks while preserving metadata.
    """

    chunks = []

    for document in documents:

        split_texts = text_splitter.split_text(
            document.page_content
        )

        for chunk_number, text in enumerate(split_texts, start=1):

            metadata = document.metadata.copy()

            metadata["chunk"] = chunk_number

            chunks.append(
                Document(
                    page_content=text,
                    metadata=metadata
                )
            )

    return chunks