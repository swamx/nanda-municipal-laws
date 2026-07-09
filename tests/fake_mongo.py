from bson import ObjectId


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
        results = [dict(doc) for doc in self._docs if self._matches(doc, filter)]
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
