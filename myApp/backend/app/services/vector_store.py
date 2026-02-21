
class VectorStore:
    def upsert(self, key: str, vector: list[float], metadata: dict | None = None) -> None:
        raise NotImplementedError

    def query(self, vector: list[float], top_k: int = 5) -> list[dict]:
        raise NotImplementedError
