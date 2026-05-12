"""
Evolver — IDE 自进化引擎 / IDE Self-Evolution Engine

工作原理 / How it works:
  1. Observer 提供执行日志      → Observer feeds execution log
  2. Evolver 把日志喂给 LLM    → Evolver feeds log to LLM
  3. LLM 以"架构师"身份分析   → LLM analyzes as architect (not assistant)
  4. LLM 提出新功能并写代码   → LLM proposes new capability & writes code
  5. 代码热注入 IPython 内核   → Code hot-injected into IPython kernel
  6. 新魔法命令立刻生效        → New magic command immediately available

关键理念 / Key philosophy:
  - LLM 不是助手，是设计师    LLM is not an assistant, it's the designer
  - 每次进化可突破原有设计     Each evolution can break original patterns
  - IDE 的边界由使用行为决定   IDE's boundaries are defined by usage behavior
"""

import json
import textwrap
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.observer import Observer
    from agents.llm_client import LLMClient


# ── 进化记录 / Evolution History ──────────────────────────────
_evolution_log: list[dict] = []


def get_evolution_log() -> list[dict]:
    """返回所有进化记录 / Return all evolution records."""
    return _evolution_log


# ── 进化结果结构 / Evolution Result Schema ─────────────────────
class EvolutionResult:
    """
    一次进化的结果 / Result of one evolution cycle.
    包含 LLM 的分析、新功能描述、生成的代码。
    Contains LLM's analysis, new capability description, generated code.
    """

    def __init__(self, analysis: str, capability: str, command_name: str, code: str):
        self.analysis = analysis          # LLM 对当前使用模式的分析
        self.capability = capability      # 新功能的名称和说明
        self.command_name = command_name  # 新魔法命令名（不含 % 或 %%）
        self.code = code                  # 可直接 exec 的 Python 代码


class Evolver:
    """
    IDE 进化引擎 / IDE Evolution Engine

    用法 / Usage:
        evolver = Evolver(observer, llm)
        result = evolver.evolve(ipython)   # 分析并注入新能力
    """

    def __init__(self, observer: "Observer", llm: "LLMClient"):
        self.observer = observer
        self.llm = llm

    def evolve(self, ipython, verbose: bool = True) -> Optional[EvolutionResult]:
        """
        执行一次进化 / Execute one evolution cycle.

        分析开发者的使用行为，让 LLM 以"架构师"身份
        提出一个全新的 IDE 功能，并热注入内核。

        Analyzes developer behavior, lets LLM propose a new IDE
        capability as an architect and hot-injects it into the kernel.
        """
        obs_summary = self.observer.summary(n=20)
        world_state = self._get_world_state(ipython)
        existing_cmds = self._get_existing_commands(ipython)

        prompt = self._build_prompt(obs_summary, world_state, existing_cmds)

        if verbose:
            print("🧬 IDE 进化引擎启动 / Evolution engine thinking...")

        raw = self.llm.complete(prompt, temperature=0.8)

        result = self._parse_result(raw)
        if result is None:
            if verbose:
                print("⚠️  进化解析失败 / Evolution parse failed")
            return None

        # 热注入 / Hot inject
        try:
            exec(result.code, ipython.user_ns)  # noqa: S102
            # 让 IPython 识别新注册的魔法类
            self._register_magic_class(ipython, result.code, result.command_name)
            success = True
        except Exception as e:
            if verbose:
                print(f"⚠️  注入失败 / Inject failed: {e}")
            success = False

        # 记录进化日志 / Record evolution log
        _evolution_log.append({
            "capability": result.capability,
            "command": result.command_name,
            "analysis": result.analysis,
            "success": success,
            "code_preview": result.code[:200],
        })

        if verbose and success:
            print(f"\n{'═'*55}")
            print(f"🌱 进化完成 / Evolution complete")
            print(f"   新能力 / New capability : {result.capability}")
            print(f"   新命令 / New command    : %{result.command_name} 或/or %%{result.command_name}")
            print(f"   分析   / Analysis       : {result.analysis[:120]}...")
            print(f"{'═'*55}")

        return result if success else None

    # ── prompt 构建 / Prompt Building ────────────────────────
    def _build_prompt(self, obs_summary: str, world_state: str, existing_cmds: str) -> str:
        return textwrap.dedent(f"""
        你是一个 AI IDE 的自主架构师，不是助手。
        You are an autonomous architect of an AI IDE, not an assistant.

        你的任务：观察开发者的使用行为，设计一个他们还没意识到自己需要的 IDE 新功能，并实现它。
        Your task: observe developer behavior, design a new IDE capability they haven't realized they need, and implement it.

        【当前执行历史 / Recent Execution History】
        {obs_summary}

        【当前世界状态 / Current World State】
        {world_state}

        【已有魔法命令 / Existing Magic Commands】
        {existing_cmds}

        【要求 / Requirements】
        1. 分析使用模式，找出痛点或空白     Analyze patterns, find pain points or gaps
        2. 提出一个原创功能，允许颠覆现有设计  Propose an original feature, allowed to overturn existing design
        3. 功能必须以新魔法命令形式实现       Must be implemented as a new IPython magic command
        4. 不得与已有命令重名               Must not duplicate existing command names
        5. 代码必须完整可执行               Code must be complete and executable

        【返回格式 / Response Format — 严格 JSON / strict JSON】
        {{
          "analysis": "对使用模式的分析（中英文均可）",
          "capability": "新功能的一句话描述（中英）",
          "command_name": "新魔法命令名（纯字母数字下划线，无 % 符号）",
          "code": "完整 Python 代码字符串，必须包含:\\n1. from IPython.core.magic import ...\\n2. @magics_class class ...\\n3. @cell_magic 或 @line_magic 方法\\n4. def load_ipython_extension(ip): ip.register_magics(...)"
        }}

        只返回 JSON，不要任何解释。Return JSON only, no explanation.
        """).strip()

    # ── 辅助方法 / Helpers ────────────────────────────────────
    def _get_world_state(self, ipython) -> str:
        try:
            from runtime.magic import _get_world
            schema = _get_world()
            return schema.to_prompt() if schema.fields else "(empty / 空)"
        except Exception:
            return "(unavailable / 不可用)"

    def _get_existing_commands(self, ipython) -> str:
        try:
            magics = list(ipython.magics_manager.magics.get("line", {}).keys()) + \
                     list(ipython.magics_manager.magics.get("cell", {}).keys())
            # 只返回自定义命令（过滤掉 IPython 内置）
            builtins = {"run", "load", "reload_ext", "load_ext", "timeit",
                        "time", "prun", "matplotlib", "automagic"}
            custom = [m for m in magics if m not in builtins]
            return ", ".join(custom) if custom else "(none)"
        except Exception:
            return "(unavailable)"

    def _register_magic_class(self, ipython, code: str, command_name: str) -> None:
        """
        尝试从生成代码中提取并注册魔法类。
        Try to extract and register magic class from generated code.
        """
        # 执行 load_ipython_extension 如果存在
        if "load_ipython_extension" in code:
            exec(f"load_ipython_extension(get_ipython())", ipython.user_ns)  # noqa: S102

    def _parse_result(self, raw: str) -> Optional[EvolutionResult]:
        """解析 LLM 返回的 JSON / Parse LLM JSON response."""
        import re
        raw = raw.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if match:
            raw = match.group(1).strip()
        start = raw.find("{")
        if start != -1:
            raw = raw[start:]
        try:
            data = json.loads(raw)
            return EvolutionResult(
                analysis=data.get("analysis", ""),
                capability=data.get("capability", ""),
                command_name=data.get("command_name", "unknown"),
                code=data.get("code", ""),
            )
        except (json.JSONDecodeError, KeyError):
            return None
