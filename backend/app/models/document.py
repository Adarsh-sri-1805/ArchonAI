from dataclasses import dataclass, field


@dataclass
class Document:
    """
    Represents a piece of text together with its metadata.
    """

    page_content: str
    metadata: dict = field(default_factory=dict)