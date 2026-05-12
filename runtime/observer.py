"""
Observer — 被动监听 IPython 执行事件

每次 cell 运行后记录：输入代码、是否成功、报错信息。
这些观察日志是 Evolver 判断"IDE 应该进化成什么"的依据。
"""

from datetime import datetime, timezone
from typing import List


class Observer:
    """
    挂载到 IPython 事件系统，无感知地追踪开发者行为。
    不影响任何现有功能。
    """

    def __init__(self, ipython, max_entries: int = 100):
        self.ip = ipython
        self.max_entries = max_entries
        self.log: List[dict] = []
        self._pending: dict = {}
        self._active = False

    def start(self) -> None:
        if self._active:
            return
        self.ip.events.register("pre_execute", self._pre_execute)
        self.ip.events.register("post_execute", self._post_execute)
        self._active = True

    def stop(self) -> None:
        if not self._active:
            return
        try:
            self.ip.events.unregister("pre_execute", self._pre_execute)
            self.ip.events.unregister("post_execute", self._post_execute)
        except ValueError:
            pass
        self._active = False

    # ── IPython hooks ────────────────────────────────────────
    def _pre_execute(self) -> None:
        raw = self.ip.history_manager.input_hist_raw
        cell = raw[-1] if raw else ""
        self._pending = {
            "cell": cell,
            "time": datetime.now(timezone.utc).isoformat(),
        }

    def _post_execute(self) -> None:
        if "cell" not in self._pending:
            # pre_execute 未触发（模块重载时的孤立事件）/ Orphaned post_execute (module reload)
            self._pending = {}
            return
        result = self.ip.last_execution_result
        entry = {
            **self._pending,
            "success": result.success if result else True,
            "error": str(result.error_in_exec) if (result and result.error_in_exec) else None,
        }
        self.log.append(entry)
        if len(self.log) > self.max_entries:
            self.log.pop(0)

    # ── 供 Evolver 使用的摘要 ─────────────────────────────────
    def summary(self, n: int = 15) -> str:
        """返回最近 n 条执行记录的文字摘要。"""
        recent = self.log[-n:]
        if not recent:
            return "(no observations yet)"
        lines = []
        for e in recent:
            status = "✓" if e["success"] else "✗ ERROR"
            preview = e["cell"].strip()[:120].replace("\n", " ↵ ")
            err = f" → {e['error']}" if e["error"] else ""
            lines.append(f"{status}  {preview}{err}")
        return "\n".join(lines)

    def error_count(self) -> int:
        return sum(1 for e in self.log if not e["success"])

    def cell_count(self) -> int:
        return len(self.log)
