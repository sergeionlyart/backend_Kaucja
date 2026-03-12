from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from legal_ingest.config import MongoConfig


@dataclass(slots=True)
class MongoRuntime:
    config: MongoConfig
    _client: MongoClient[dict[str, Any]] | None = None

    def __enter__(self) -> "MongoRuntime":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def client(self) -> MongoClient[dict[str, Any]]:
        if self._client is None:
            raise RuntimeError("Mongo client is not connected.")
        return self._client

    @property
    def db(self) -> Database[dict[str, Any]]:
        return self.client[self.config.db_name]

    def connect(self) -> None:
        if self._client is not None:
            return
        self._client = MongoClient(
            self.config.uri,
            serverSelectionTimeoutMS=5_000,
            tz_aware=True,
        )
        self._client.admin.command("ping")

    def close(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None

    def collection(self, name: str) -> Collection[dict[str, Any]]:
        return self.db[name]

    def count_documents(self, name: str) -> int:
        return self.collection(name).count_documents({})

    def get_collection_counts(self, names: Iterable[str]) -> dict[str, int]:
        return {name: self.count_documents(name) for name in names}

    def load_collection(
        self,
        name: str,
        *,
        projection: dict[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        cursor = self.collection(name).find({}, projection=projection)
        return list(cursor)

    def iter_collection(
        self,
        name: str,
        *,
        projection: dict[str, int] | None = None,
    ):
        return self.collection(name).find({}, projection=projection)
