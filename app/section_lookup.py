from pymongo.database import Database

from app.db import LAWS_COLLECTION


def get_section_chunks(db: Database, section_number: str) -> list[dict]:
    """All chunks sharing a section_number, ordered by chunk_index (a long
    section may have been split by the chunker into multiple chunks).
    """
    chunks = list(db[LAWS_COLLECTION].find({"type": "chunk", "section_number": section_number}))
    return sorted(chunks, key=lambda c: c["chunk_index"])
