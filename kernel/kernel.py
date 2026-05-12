"""
Kernel — world-platform 核心运行时 / World-Platform Core Runtime

提供两个高层抽象 / Provides two high-level abstractions:

┌─────────────────────────────────────────────────────────────┐
│  WorldKernel                                                │
│  统一内核对象：Schema + Trace + Memory + Planner 一体化    │
│  Unified kernel: Schema + Trace + Memory + Planner          │
│  与 magic 系统共享状态，支持快照/恢复                       │
│  Shares state with magic system; supports snapshot/restore  │
├─────────────────────────────────────────────────────────────┤
│  Pipeline                                                   │
│  可链式调用的多步 LLM 流水线                               │
│  Chainable multi-step LLM pipeline                          │
│  每步输出自动成为下步输入 / Each step's output → next input │
└─────────────────────────────────────────────────────────────┘

设计原则 / Design principles:
- WorldKernel 是 Agent + Magic 的统一入口，不是第三套 API
  WorldKernel is a unified entry point for Agent + Magic, not a third API
- Pipeline 补充 Workflow/Cell 的命令式风格，提供声明式链式语法
  Pipeline complements Workflow/Cell's imperative style with declarative chaining
"""

from __future__ import annotations

import copy
from typing import Any, List, Optional

from runtime.schema import Schema
from runtime.trace import Trace
from runtime.worlddb import WorldDB
from runtime.memory import Memory
from runtime.planner import Planner
from agents.llm_client import LLMClient


# ═══════════════════════════════════════════════════════════════
# WorldKernel — 统一运行时内核 / Unified Runtime Kernel
# ═══════════════════════════════════════════════════════════════

class WorldKernel:
    """
    统一运行时内核，把所有 runtime 组件聚合到一个对象。
    Unified runtime kernel aggregating all runtime components.

    特性 / Features:
    - 与 magic.py 全局状态共享 Schema（%%world 和代码互通）
      Shares Schema with magic.py global state (%%world ↔ code)
    - snapshot(name) / restore(name) 世界状态快照与恢复
      snapshot(name) / restore(name) for world state versioning
    - plan(goal) 直接调用 LLM 自动规划
      plan(goal) calls LLM for auto-planning

    用法 / Usage:
        from kernel import WorldKernel
        k = WorldKernel(api_key="sk-...")
        k.set("project", "world-platform")
        k.snapshot("v1")
        k.set("status", "in-progress")
        k.restore("v1")   # 回滚 / rollback
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        base_url: Optional[str] = None,
        memory_path: Optional[str] = None,
        sync_magic: bool = True,
    ):
        # 核心运行时组件 / Core runtime components
        self.schema = Schema()
        self.trace = Trace()
        self.db = WorldDB()
        self.memory = Memory(path=memory_path)
        self.planner = Planner(model=model, api_key=api_key, base_url=base_url)

        # LLM 客户端（供 Pipeline 等复用）/ LLM client (shared)
        self._llm_kwargs = dict(model=model, api_key=api_key, base_url=base_url)

        # 世界状态快照仓库 / World state snapshot store
        self._snapshots: dict[str, dict] = {}

        # 与 magic.py 全局状态同步 / Sync schema to magic.py global state
        if sync_magic:
            self._sync_to_magic()

    # ── 与 magic 系统同步 / Sync with magic system ──────────────

    def _sync_to_magic(self) -> None:
        """
        将本内核的 Schema 注入为 magic.py 的全局状态。
        Inject this kernel's Schema as magic.py's global state.
        之后 %%world / %%dev 操作的是同一个 Schema。
        After this, %%world / %%dev operate on the same Schema.
        """
        try:
            import runtime.magic as _magic
            _magic._world_schema = self.schema
        except ImportError:
            pass

    # ── 世界状态 CRUD / World State CRUD ────────────────────────

    def set(self, key: str, value: Any) -> None:
        """写入世界状态字段 / Write a world state field."""
        self.schema.set(key, value)
        self.trace.log("set", {key: value})

    def get(self, key: str) -> Any:
        """读取世界状态字段 / Read a world state field."""
        return self.schema.get(key)

    def update(self, data: dict) -> None:
        """批量写入字段（来自 dict）/ Batch-write fields from dict."""
        self.schema.from_llm(data)
        self.trace.log("update", data)

    # ── 快照 / Snapshot ─────────────────────────────────────────

    def snapshot(self, name: str = "default") -> None:
        """
        保存当前世界状态快照 / Save a snapshot of the current world state.

        k.snapshot("before_experiment")
        k.set("flag", "risky_change")
        k.restore("before_experiment")  # 回滚 / rollback
        """
        self._snapshots[name] = copy.deepcopy(self.schema.to_dict())
        self.trace.log("snapshot", {"name": name, "fields": list(self._snapshots[name].keys())})

    def restore(self, name: str = "default") -> None:
        """
        从快照恢复世界状态 / Restore world state from a snapshot.
        恢复后自动重新同步 magic 全局状态。
        Re-syncs magic global state after restore.
        """
        data = self._snapshots.get(name)
        if data is None:
            raise KeyError(f"Snapshot '{name}' not found. Available: {list(self._snapshots)}")
        self.schema = Schema()
        self.schema.from_llm(data)
        self._sync_to_magic()
        self.trace.log("restore", {"name": name})

    def list_snapshots(self) -> List[str]:
        """列出所有快照名 / List all snapshot names."""
        return list(self._snapshots.keys())

    # ── 规划 / Planning ─────────────────────────────────────────

    def plan(self, goal: str, context: dict = None) -> List[str]:
        """
        用 LLM 自动规划步骤列表 / Auto-plan steps with LLM.
        上下文默认为当前世界状态 / Context defaults to current world state.
        """
        ctx = context if context is not None else self.schema.to_dict()
        steps = self.planner.plan(goal, ctx)
        self.trace.log("plan", {"goal": goal, "steps": steps})
        return steps

    # ── 持久化 / Persistence ─────────────────────────────────────

    def save(self, key: str, value: Any) -> None:
        """写入 WorldDB / Write to WorldDB."""
        self.db.save(key, value)

    def load(self, key: str) -> Any:
        """从 WorldDB 读取 / Read from WorldDB."""
        return self.db.load(key)

    def remember(self, key: str, value: Any, tags: List[str] = None) -> None:
        """写入长期记忆 / Write to long-term memory."""
        self.memory.remember(key, value, tags)

    def recall(self, key: str) -> Any:
        """读取最近记忆 / Recall most recent memory."""
        return self.memory.recall(key)

    # ── 观察 / Observation ───────────────────────────────────────

    def state(self) -> str:
        """返回当前世界状态的文字摘要（LLM prompt 格式）。
        Return world state summary in LLM prompt format."""
        return self.schema.to_prompt() if self.schema.fields else "## World State\n*(empty)*"

    def history(self, n: int = 20) -> List[dict]:
        """返回最近 n 条 Trace 事件 / Return last n Trace events."""
        return self.trace.events[-n:]

    # ── 便捷打印 / Display helpers ───────────────────────────────

    def __repr__(self) -> str:
        fields = list(self.schema.fields.keys())
        snaps = list(self._snapshots.keys())
        return (
            f"<WorldKernel fields={fields} "
            f"snapshots={snaps} "
            f"trace_events={len(self.trace.events)}>"
        )


# ═══════════════════════════════════════════════════════════════
# Pipeline — 可链式的多步 LLM 流水线 / Chainable Multi-Step LLM Pipeline
# ═══════════════════════════════════════════════════════════════

class Pipeline:
    """
    声明式多步 LLM 流水线。
    Declarative multi-step LLM pipeline.

    每步的输出自动作为下步的 {{input}}，支持链式调用。
    Each step's output becomes the next step's {{input}}; supports chaining.

    用法 / Usage:
        from kernel import Pipeline

        result = (
            Pipeline(api_key="sk-...")
            .step("Extract key requirements from: {{input}}")
            .step("Convert requirements into a numbered task list: {{input}}")
            .step("Estimate effort (S/M/L) for each task: {{input}}")
            .run_final("Build a user authentication system")
        )
        print(result)

    高级用法 / Advanced usage:
        pipe = Pipeline(api_key="sk-...")
        pipe.step("Summarize this in one sentence: {{input}}")
        pipe.step("Translate the summary to Chinese: {{input}}")

        all_results = pipe.run("Long article text here...")
        # all_results[0] = English summary
        # all_results[1] = Chinese translation
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        base_url: Optional[str] = None,
        temperature: float = 0.7,
    ):
        self._steps: List[str] = []   # prompt 模板列表 / Prompt template list
        self._llm = LLMClient(
            model=model,
            api_key=api_key or "",
            base_url=base_url or "https://api.deepseek.com",
        )
        self._temperature = temperature

    # ── 构建流水线 / Build pipeline ─────────────────────────────

    def step(self, prompt_template: str) -> "Pipeline":
        """
        添加一个流水线步骤（返回 self，支持链式调用）。
        Add a pipeline step (returns self for chaining).

        在 prompt_template 中用 {{input}} 引用上一步的输出。
        Use {{input}} in prompt_template to reference previous step output.
        """
        self._steps.append(prompt_template)
        return self

    # ── 执行流水线 / Execute pipeline ────────────────────────────

    def run(self, input: str) -> List[str]:
        """
        顺序执行所有步骤，返回每步输出列表。
        Execute all steps in order; return list of each step's output.
        """
        results: List[str] = []
        current = input
        for template in self._steps:
            prompt = template.replace("{{input}}", current)
            current = self._llm.complete(prompt, temperature=self._temperature)
            results.append(current)
        return results

    def run_final(self, input: str) -> str:
        """
        执行流水线并只返回最终结果。
        Execute pipeline and return only the final result.
        """
        outputs = self.run(input)
        return outputs[-1] if outputs else input

    def run_stream(self, input: str):
        """
        流式执行最后一步（前几步非流式）。
        Stream the last step (preceding steps run non-streaming).

        适合最后一步是生成长文本的场景。
        Useful when the last step generates long text.
        """
        if not self._steps:
            return

        # 前 n-1 步正常执行 / Run first n-1 steps normally
        current = input
        for template in self._steps[:-1]:
            prompt = template.replace("{{input}}", current)
            current = self._llm.complete(prompt, temperature=self._temperature)

        # 最后一步流式输出 / Stream the last step
        last_prompt = self._steps[-1].replace("{{input}}", current)
        yield from self._llm.stream(last_prompt, temperature=self._temperature)

    # ── 观察 / Inspection ───────────────────────────────────────

    def __len__(self) -> int:
        return len(self._steps)

    def __repr__(self) -> str:
        previews = [s[:40].replace("\n", " ") + "…" for s in self._steps]
        return f"<Pipeline steps={len(self._steps)} {previews}>"
