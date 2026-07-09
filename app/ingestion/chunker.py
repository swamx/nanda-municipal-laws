from dataclasses import dataclass

from app.ingestion.parser import SectionChunk

MAX_CHUNK_CHARS = 2000


@dataclass
class PersistableChunk:
    section_number: str
    section_title: str
    text: str
    chunk_index: int
    anchor_id: str


def _split_text(text: str, max_chars: int) -> list[str]:
    sentences = text.split(". ")
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current}. {sentence}" if current else sentence
        if len(candidate) > max_chars and current:
            parts.append(current.strip())
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current.strip())
    return parts


def chunk_section(section: SectionChunk, max_chars: int = MAX_CHUNK_CHARS) -> list[PersistableChunk]:
    if len(section.text) <= max_chars:
        return [
            PersistableChunk(
                section_number=section.section_number,
                section_title=section.section_title,
                text=section.text,
                chunk_index=0,
                anchor_id=section.anchor_id,
            )
        ]

    return [
        PersistableChunk(
            section_number=section.section_number,
            section_title=section.section_title,
            text=part,
            chunk_index=index,
            anchor_id=section.anchor_id,
        )
        for index, part in enumerate(_split_text(section.text, max_chars))
    ]
