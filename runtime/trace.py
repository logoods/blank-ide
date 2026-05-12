import time
from typing import List


class Trace:
    """
    事件审计日志 / Event audit log.
    记录所有 Agent 操作，用于调试和追溯。
    Records all Agent operations for debugging and tracing.
    """

    def __init__(self):
        self.events: List[dict] = []  # 事件列表 / Event list

    def log(self, event: str, data=None) -> None:
        """追加一条带时间戳的事件 / Append a timestamped event."""
        self.events.append({
            "time": time.time(),  # Unix 时间戳 / Unix timestamp
            "event": event,       # 事件类型 / Event type
            "data": data          # 附加数据 / Attached data
        })
