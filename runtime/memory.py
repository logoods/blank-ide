import json
import os
from datetime import datetime, timezone
from typing import Any, List, Optional


class Memory:
    """
    长期记忆模块 / Long-term memory module.
    - 内存存储 + 可选 JSON 文件持久化
      In-memory storage + optional JSON file persistence
    - remember(key, value, tags) / recall(key) / search(tag)
    """

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self.entries: List[dict] = []
        if path and os.path.exists(path):
            self._load()

    def remember(self, key: str, value: Any, tags: List[str] = None) -> None:
        entry = {
            "key": key,
            "value": value,
            "tags": tags or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.entries.append(entry)
        if self.path:
            self._save()

    def recall(self, key: str) -> Any:
        """返回最近一条匹配 key 的值，不存在返回 None。
        Return the most recent value matching key, or None if not found."""
        matches = [e for e in self.entries if e["key"] == key]
        return matches[-1]["value"] if matches else None

    def recall_all(self, key: str) -> List[Any]:
        """返回所有匹配 key 的值列表。
        Return a list of all values matching key."""
        return [e["value"] for e in self.entries if e["key"] == key]

    def search(self, tag: str) -> List[dict]:
        """按 tag 搜索，返回完整 entry 列表。
        Search by tag, return full entry list."""
        return [e for e in self.entries if tag in e.get("tags", [])]

    def clear(self) -> None:
        self.entries = []
        if self.path:
            self._save()

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            self.entries = json.load(f)
