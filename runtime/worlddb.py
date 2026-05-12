class WorldDB:
    """
    世界持久化存储（内存 KV，可接持久化后端）。
    World persistent storage (in-memory KV, pluggable backend).
    """

    def __init__(self):
        self.storage = {}  # 内存存储 / In-memory storage

    def save(self, key: str, value) -> None:
        """写入键值对 / Write key-value pair."""
        self.storage[key] = value

    def load(self, key: str):
        """读取键值对，不存在返回 None / Read key-value, returns None if missing."""
        return self.storage.get(key)
