import sys

from pymongo import ASCENDING, MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure

from app.config import settings

# Single collection, storing both document ("type": "document") and chunk
# ("type": "chunk") records - the Atlas user's role only grants read/write
# (no createIndex) on "dl-laws".
LAWS_COLLECTION = "dl-laws"

_client = MongoClient(
    settings.mongo_atlas_conn_str,
    connectTimeoutMS=settings.mongo_connect_timeout_ms,
    serverSelectionTimeoutMS=settings.mongo_server_selection_timeout_ms,
)
_db = _client[settings.mongodb_db_name]


def get_db() -> Database:
    return _db


def ping(db: Database | None = None) -> bool:
    db = db if db is not None else get_db()
    db.command("ping")
    return True


TEXT_INDEX_NAME = "chunks_text_idx"


def ensure_indexes(db: Database | None = None) -> None:
    """Best-effort: if the Atlas role in use doesn't grant createIndex, a
    warning is logged and search falls back to in-app scoring (see
    app/search_scoring.py and app/retrieval.py) instead of relying on this
    text index.
    """
    db = db if db is not None else get_db()
    laws = db[LAWS_COLLECTION]

    index_specs = [
        (
            "source_url",
            {"unique": True, "name": "documents_source_url_uidx", "partialFilterExpression": {"type": "document"}},
        ),
        (
            [("document_id", ASCENDING), ("chunk_index", ASCENDING)],
            {"name": "chunks_document_order_idx", "partialFilterExpression": {"type": "chunk"}},
        ),
        (
            "section_number",
            {"name": "chunks_section_number_idx", "partialFilterExpression": {"type": "chunk"}},
        ),
        (
            [("section_title", "text"), ("text", "text")],
            {
                "name": TEXT_INDEX_NAME,
                "weights": {"section_title": 5, "text": 1},
                "partialFilterExpression": {"type": "chunk"},
            },
        ),
    ]

    for keys, options in index_specs:
        try:
            laws.create_index(keys, **options)
        except OperationFailure as exc:
            print(f"warning: could not create index {options.get('name')}: {exc}", file=sys.stderr)
