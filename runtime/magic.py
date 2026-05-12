"""
Blank IDE 魔法命令系统

───────────────────────────────────────────────────────────
%%dev  [--stream | --exec | --plan]
    自然语言 → LLM → Markdown 输出（默认）
    --stream  流式打印
    --exec    自动执行 IDECommand（白板模式核心）
    --plan    自动规划步骤列表

%%world
    自然语言描述 → LLM 解析 → 写入全局 Schema（世界状态）
    用法：
        %%world
        项目名是 my-app，当前阶段是开发中，负责人是 Alice

%world_state
    打印当前世界状态（Schema）

%world_clear
    清空世界状态
───────────────────────────────────────────────────────────

可选环境变量：
    DEEPSEEK_API_KEY   API Key
    DEEPSEEK_BASE_URL  Base URL（默认 https://api.deepseek.com）
    DEEPSEEK_MODEL     模型名（默认 deepseek-chat）
"""

import os
import json
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.display import display, Markdown

# ── 全局单例 / Global singletons ─────────────────────────────
_world_schema = None   # 世界状态 / World state schema
_observer = None       # 执行监听器 / Execution observer
_evolver = None        # 进化引擎 / Evolution engine


def _get_observer(ipython=None):
    """获取或创建 Observer 单例 / Get or create Observer singleton."""
    global _observer
    if _observer is None and ipython is not None:
        from runtime.observer import Observer
        _observer = Observer(ipython)
        _observer.start()
    return _observer


def _get_evolver(ipython=None):
    """获取或创建 Evolver 单例 / Get or create Evolver singleton."""
    global _evolver
    if _evolver is None and ipython is not None:
        obs = _get_observer(ipython)
        llm = _get_llm()
        from runtime.evolver import Evolver
        _evolver = Evolver(obs, llm)
    return _evolver


def _get_world():
    global _world_schema
    if _world_schema is None:
        from runtime.schema import Schema
        _world_schema = Schema()
    return _world_schema


def _get_llm():
    from agents.llm_client import LLMClient
    return LLMClient(
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )


# ── 执行 IDECommand ───────────────────────────────────────
def _execute_command(cmd, schema, ipython):
    """把 IDECommand 落地到 Jupyter 环境"""
    from IPython.display import display, Markdown
    from runtime.command import IDECommand

    action = cmd.action

    if action == "set_field":
        value = cmd.params.get("value", cmd.params)
        schema.set(cmd.target, value)
        display(Markdown(f"✅ **set_field** `{cmd.target}` = `{value}`"))

    elif action == "run_cell":
        code = cmd.params.get("code", "")
        if code:
            display(Markdown(f"▶️ **run_cell**\n```python\n{code}\n```"))
            ipython.run_cell(code)
        else:
            display(Markdown(f"⚠️ run_cell: no `code` in params"))

    elif action == "create_cell":
        code = cmd.params.get("code", "# new cell")
        display(Markdown(f"📝 **create_cell** — 以下代码已生成（请手动新建单元格粘贴运行）：\n```python\n{code}\n```"))

    elif action == "show_panel":
        content = cmd.params.get("content", schema.to_prompt())
        display(Markdown(f"### 📊 {cmd.target or 'Panel'}\n{content}"))

    elif action == "log":
        msg = cmd.params.get("message", cmd.description)
        display(Markdown(f"📋 **log**: {msg}"))

    elif action == "plan":
        steps = cmd.params.get("steps", [])
        if steps:
            lines = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
            display(Markdown(f"📌 **plan**\n{lines}"))
        else:
            display(Markdown(f"📌 **plan**: {cmd.description}"))

    elif action == "run_workflow":
        display(Markdown(f"⚙️ **run_workflow** `{cmd.target}` — {cmd.description}"))

    else:
        # 识别 custom + commands 数组（LLM 自然输出的 batch 模式）
        nested_commands = cmd.params.get("commands", [])
        if nested_commands and isinstance(nested_commands, list):
            for item in nested_commands:
                try:
                    sub = IDECommand.model_validate(item)
                    _execute_command(sub, schema, ipython)
                except Exception:
                    pass
            return

        # 识别 custom + updates 数组
        updates = cmd.params.get("updates", [])
        if updates and isinstance(updates, list):
            msgs = []
            for item in updates:
                field = item.get("field") or item.get("key") or item.get("name")
                value = item.get("value")
                if field is not None and value is not None:
                    schema.set(field, value)
                    msgs.append(f"✅ **set_field** `{field}` = `{value}`")
            if msgs:
                display(Markdown("\n\n".join(msgs)))
                return

        # 泛化处理：把所有顶层 key-value 参数直接写入 Schema（跳过嵌套对象和列表）
        flat_updates = {
            k: v for k, v in cmd.params.items()
            if not isinstance(v, (dict, list))
        }
        if flat_updates:
            msgs = []
            for k, v in flat_updates.items():
                schema.set(k, v)
                msgs.append(f"✅ **set_field** `{k}` = `{v}`")
            display(Markdown("\n\n".join(msgs)))
        else:
            display(Markdown(f"🔧 **{action}** `{cmd.target or ''}` — {cmd.description}\n```json\n{json.dumps(cmd.params, ensure_ascii=False, indent=2)}\n```"))


# ── 魔法命令类 ────────────────────────────────────────────
@magics_class
class WorldMagics(Magics):

    # ── %%dev ────────────────────────────────────────────
    @cell_magic
    def dev(self, line: str, cell: str):
        """
        %%dev [--stream | --exec | --plan]

        --stream  流式输出（纯对话模式）
        --exec    白板模式：LLM 返回 IDECommand，自动执行并更新 Schema
        --plan    规划模式：返回步骤列表
        默认：自然语言问答，Markdown 渲染
        """
        schema = _get_world()
        llm = _get_llm()
        flags = set(line.strip().split())

        # 注入世界状态上下文
        world_context = schema.to_prompt() if schema.fields else ""

        if "--exec" in flags:
            # ── 白板模式：LLM → IDECommandBatch → 逐条执行 ──
            from runtime.command import IDECommandBatch
            prompt = (
                f"{world_context}\n\n"
                f"你是一个 IDE Agent。根据世界状态和用户指令，决定 IDE 下一步执行什么动作。\n\n"
                f"用户指令：{cell.strip()}\n\n"
                f"返回一个 IDECommandBatch JSON（可包含多条 IDECommand）。"
            )
            display(Markdown("🤖 **IDE Agent 思考中…**"))
            batch = llm.complete_structured(prompt, IDECommandBatch)
            display(Markdown(f"---\n**目标**: {batch.goal or cell.strip()}  \n**指令数**: {len(batch)}\n---"))
            for cmd in batch:
                _execute_command(cmd, schema, self.shell)

        elif "--plan" in flags:
            # ── 规划模式：LLM → 步骤列表 ─────────────────
            from runtime.planner import Planner
            planner = Planner(
                model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
                api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
                base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            )
            steps = planner.plan(cell.strip(), context=schema.to_dict())
            lines = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
            display(Markdown(f"## 📌 规划结果\n{lines}"))

        elif "--stream" in flags:
            # ── 流式对话模式 ──────────────────────────────
            prompt = f"{world_context}\n\n{cell.strip()}" if world_context else cell.strip()
            for chunk in llm.stream(prompt):
                print(chunk, end="", flush=True)
            print()

        else:
            # ── 默认：问答模式，Markdown 渲染 ─────────────
            prompt = f"{world_context}\n\n{cell.strip()}" if world_context else cell.strip()
            result = llm.complete(prompt)
            display(Markdown(result))

    # ── %%world ──────────────────────────────────────────
    @cell_magic
    def world(self, line: str, cell: str):
        """
        %%world
        用自然语言描述世界状态，LLM 解析为 key-value 写入 Schema。
        """
        schema = _get_world()
        llm = _get_llm()

        prompt = (
            f"从以下自然语言描述中提取结构化字段，返回一个 JSON 对象（key-value 格式，不要嵌套）。\n\n"
            f"描述：{cell.strip()}\n\n"
            f"只返回 JSON，不要解释。"
        )
        raw = llm.complete(prompt, temperature=0.1)

        # 提取 JSON
        import re
        raw = raw.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        raw = match.group(1).strip() if match else raw
        # 去掉非 JSON 前缀
        start = raw.find("{")
        if start != -1:
            raw = raw[start:]

        try:
            data = json.loads(raw)
            schema.from_llm(data)
            display(Markdown(f"✅ **世界状态已更新**\n\n{schema.to_prompt()}"))
        except json.JSONDecodeError as e:
            display(Markdown(f"⚠️ 解析失败：{e}\n\n原始输出：\n```\n{raw}\n```"))

    # ── %world_state ─────────────────────────────────────
    @line_magic
    def world_state(self, line: str):
        """%world_state  — 打印当前世界状态"""
        schema = _get_world()
        display(Markdown(schema.to_prompt() if schema.fields else "## World State\n*(empty)*"))

    # ── %world_clear ─────────────────────────────────────
    @line_magic
    def world_clear(self, line: str):
        """%world_clear  — 清空世界状态 / Clear world state"""
        global _world_schema
        from runtime.schema import Schema
        _world_schema = Schema()
        display(Markdown("🗑️ **世界状态已清空 / World state cleared**"))

    # ── %ide_evolve ──────────────────────────────────────────
    @line_magic
    def ide_evolve(self, line: str):
        """
        %ide_evolve
        触发一次 IDE 自进化 / Trigger one IDE self-evolution cycle.

        IDE 分析你的使用行为，自主设计并注入一个新功能。
        IDE analyzes your behavior, autonomously designs and injects a new capability.
        """
        evolver = _get_evolver(self.shell)
        if evolver is None:
            display(Markdown("⚠️ Evolver 未初始化 / Evolver not initialized"))
            return
        evolver.evolve(self.shell, verbose=True)

    # ── %ide_history ─────────────────────────────────────────
    @line_magic
    def ide_history(self, line: str):
        """
        %ide_history
        查看所有 IDE 进化历史（自主进化 + 用户定义）。
        View all IDE evolution history (autonomous + user-defined).
        """
        from runtime.evolver import get_evolution_log
        import runtime.ide_evolution as evo

        # 自主进化记录（%ide_evolve）/ Autonomous evolutions (%ide_evolve)
        auto_log = get_evolution_log()
        # 用户定义扩展（%%ide）/ User-defined extensions (%%ide)
        user_log = evo.list_extensions()

        if not auto_log and not user_log:
            display(Markdown(
                "*(IDE 尚未进化 / IDE has not evolved yet)\n\n"
                "- 自主进化 / Autonomous: `%ide_evolve`\n"
                "- 自定义能力 / Custom capability: `%%ide`*"
            ))
            return

        sections = []

        if auto_log:
            lines = [f"## 🧬 自主进化 / Autonomous Evolutions ({len(auto_log)} 次/times)\n"]
            for i, e in enumerate(auto_log, 1):
                status = "✅" if e["success"] else "❌"
                lines.append(
                    f"### {i}. {status} `%{e['command']}`\n"
                    f"**功能 / Capability**: {e['capability']}\n\n"
                    f"**分析 / Analysis**: {e['analysis'][:200]}...\n"
                )
            sections.append("\n".join(lines))

        if user_log:
            rows = ["| # | 名称/Name | 描述/Request | 状态/Status | 时间/Time |",
                    "|---|-----------|--------------|-------------|----------|"]  
            for i, h in enumerate(user_log, 1):
                status = "✅" if h.get("success") else "❌"
                ts = h.get("created_at", "")[:16].replace("T", " ")
                req = h.get("request", "")[:40]
                rows.append(f"| {i} | `{h['name']}` | {req} | {status} | {ts} |")
            sections.append(f"## 🔧 自定义能力 / Custom Capabilities ({len(user_log)} 个/items)\n\n" + "\n".join(rows))

        display(Markdown("\n\n---\n\n".join(sections)))

    # ── %ide_observe ─────────────────────────────────────────
    @line_magic
    def ide_observe(self, line: str):
        """
        %ide_observe
        查看 Observer 当前观察到的执行记录 / View current observation log.
        """
        obs = _get_observer(self.shell)
        if obs is None or not obs.log:
            display(Markdown("*(尚无执行记录 / No execution records yet)*"))
            return
        display(Markdown(
            f"## 👁 执行观察日志 / Execution Observation Log\n"
            f"- 总执行次数 / Total executions : **{obs.cell_count()}**\n"
            f"- 错误次数   / Error count      : **{obs.error_count()}**\n\n"
            f"**最近记录 / Recent records**:\n```\n{obs.summary(10)}\n```"
        ))

    # ── %%ide ────────────────────────────────────────────
    @cell_magic
    def ide(self, line: str, cell: str):
        """
        %%ide
        用自然语言描述新的 IDE 能力，Agent 自动生成代码并注册。

        例：
            %%ide
            给IDE加一个 %schema_table 命令，把世界状态渲染成 Markdown 表格

        IDE 会立刻拥有 %schema_table，且下次启动自动恢复。
        """
        import runtime.ide_evolution as evo
        schema = _get_world()
        world_context = schema.to_prompt()

        display(Markdown("🧬 **IDE 进化中…** Agent 正在为 IDE 开发新能力"))

        result = evo.evolve(
            request=cell.strip(),
            world_context=world_context,
            ipython=self.shell,
        )

        if result["success"]:
            display(Markdown(
                f"✅ **新能力已注册**: `{result['name']}`\n\n"
                f"```python\n{result['code']}\n```"
            ))
        else:
            display(Markdown(
                f"⚠️ **注册失败**: `{result['name']}`\n\n"
                f"**错误**: {result['error']}\n\n"
                f"**生成代码**:\n```python\n{result['code']}\n```"
            ))




def load_ipython_extension(ipython):
    ipython.register_magics(WorldMagics)
    # 自动启动 Observer，无感知地监听所有执行
    # Automatically start Observer to silently monitor all executions
    _get_observer(ipython)
    print("✓ Blank IDE 已加载 / Blank IDE loaded")
    print("  %ide_evolve    — 触发 IDE 进化    / Trigger IDE evolution")
    print("  %ide_history   — 查看进化历史     / View evolution history")
    print("  %ide_observe   — 查看执行观察日志 / View observation log")
    print("  %%world        — 自然语言写世界状态 / Write world state in natural language")
    print("  %%dev [--exec|--plan|--stream]  — AI 助手 / AI assistant")

    # 启动时自动恢复所有历史进化扩展
    import runtime.ide_evolution as evo
    loaded = evo.load_all(ipython)
    if loaded:
        print(f"✓ IDE 历史扩展已恢复: {loaded}")

