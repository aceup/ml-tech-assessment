from dataclasses import dataclass


@dataclass
class Summary:
    id: str
    content: str
    ctas: list[str]
