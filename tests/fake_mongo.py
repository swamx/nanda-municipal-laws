import re

from bson import ObjectId

_WORD_RE = re.compile(r"\w+")


def _text_score(doc: dict, query: str) -> float:
    """Approximates MongoDB's $text/textScore (title weighted over body) so
    tests can exercise the text_index retrieval path without a real index.
    """
    words = _WORD_RE.findall(query.lower())
    title = doc.get("section_title", "").lower()
    body = doc.get("text", "").lower()
    score = 0.0
    for word in words:
        score += title.count(word) * 5
        score += body.count(word)
    return score


class FakeCursor:
    def __init__(self, docs: list[dict]):
        self._docs = list(docs)

    def sort(self, *args, **kwargs) -> "FakeCursor":
        return self

    def limit(self, n: int) -> "FakeCursor":
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


class FakeLawsCollection:
    """Approximates the single `dl-laws` collection (mixed document/chunk
    records distinguished by a "type" field) with plain equality filtering.
    Ranking/scoring happens in app.search_scoring, exercised the same way
    whether the caller is this fake or a real MongoDB collection.
    """

    def __init__(self):
        self._docs: list[dict] = []

    def delete_many(self, filter: dict) -> None:
        self._docs = [d for d in self._docs if not self._matches(d, filter)]

    def insert_many(self, docs: list[dict]) -> None:
        for doc in docs:
            doc.setdefault("_id", ObjectId())
            self._docs.append(doc)

    def create_index(self, *args, **kwargs) -> None:
        pass

    def find_one_and_update(self, filter: dict, update: dict, upsert: bool = False, return_document=None) -> dict:
        for doc in self._docs:
            if self._matches(doc, filter):
                self._apply_update(doc, update)
                return doc
        doc = {"_id": ObjectId(), **filter}
        self._apply_update(doc, update)
        self._docs.append(doc)
        return doc

    @staticmethod
    def _apply_update(doc: dict, update: dict) -> None:
        doc.update(update.get("$set", {}))
        for key, amount in update.get("$inc", {}).items():
            doc[key] = doc.get(key, 0) + amount

    def find_one(self, filter: dict):
        for doc in self._docs:
            if self._matches(doc, filter):
                return doc
        return None

    def find(self, filter: dict | None = None, projection: dict | None = None) -> FakeCursor:
        filter = filter or {}
        text_query = None
        equality_filter = {}
        for key, value in filter.items():
            if key == "$text":
                text_query = value["$search"]
            else:
                equality_filter[key] = value

        results = []
        for doc in self._docs:
            if not self._matches(doc, equality_filter):
                continue
            if text_query is not None:
                score = _text_score(doc, text_query)
                if score <= 0:
                    continue
                scored = dict(doc)
                scored["score"] = score
                results.append(scored)
            else:
                results.append(dict(doc))

        if text_query is not None:
            results.sort(key=lambda d: d["score"], reverse=True)

        return FakeCursor(results)

    @staticmethod
    def _matches(doc: dict, filter: dict) -> bool:
        return all(doc.get(key) == value for key, value in filter.items())


class FakeDatabase:
    def __init__(self):
        self.laws = FakeLawsCollection()
        self._collections = {"dl-laws": self.laws}

    def __getitem__(self, name: str):
        return self._collections[name]

    def command(self, name: str) -> dict:
        return {"ok": 1.0}
