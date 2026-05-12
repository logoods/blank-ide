"""
IDE 自进化引擎

用户说"给 IDE 加个功能" → LLM 生成魔法命令代码
→ 写入 runtime/ide_extensions/<name>.py
→ 动态注册到 IPython
→ IDE 立刻拥有新能力，且下次启动自动恢复

流程：
    %%ide
    给IDE加一个 %schema_table 命令，把世界状态渲染成 Markdown 表格

    → LLM 生成代码 → 注册 → 立刻可用
"""

import os
import re
import json
import importlib
import textwrap
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

EXTENSIONS_DIR = Path(__file__).parent / "ide_extensions"
HISTORY_FILE = EXTENSIONS_DIR / "_history.json"


# ── 进化历史记录 ────────────────────────────────────────────
def _load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_history(history: list) -> None:
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── 生成扩展代码 ────────────────────────────────────────────
_CODEGEN_PROMPT = """你是一个 IDE 扩展开发 Agent。
你的任务：根据用户描述，生成一个 IPython 魔法命令的 Python 代码。

要求：
1. 代码必须定义一个函数或类，包含魔法命令逻辑
2. 最后必须有一行注册语句：`ip.register_magic_function(fn, magic_kind='line')` 或 `ip.register_magics(MyMagic)`
3. 可以 import 项目模块：from runtime.magic import _get_world, _get_llm
4. `ip` 是 IPython shell 实例，会在执行时注入
5. 不要包含 load_ipython_extension，不要重新注册已有命令
6. 代码要简洁可运行，不要注释过多

世界状态上下文：
{world_context}

用户需求：
{request}

只返回纯 Python 代码，不要 markdown 代码块，不要解释。
"""


def evolve(request: str, world_context: str, ipython) -> dict:
    """
    主入口：用自然语言描述新功能，生成并注册到 IDE。
    返回 {"name": str, "code": str, "success": bool, "error": str}
    """
    from agents.llm_client import LLMClient

    llm = LLMClient(
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )

    # 1. LLM 生成代码
    prompt = _CODEGEN_PROMPT.format(
        world_context=world_context or "(empty)",
        request=request,
    )
    raw_code = llm.complete(prompt, temperature=0.2)

    # 清理 markdown 代码块
    raw_code = raw_code.strip()
    match = re.search(r"```(?:python)?\s*([\s\S]+?)```", raw_code)
    if match:
        raw_code = match.group(1).strip()

    # 2. 推断命令名（从代码里找 register_magic_function 或 def %xxx）
    name = _infer_name(raw_code, request)

    # 3. 写入文件（持久化）
    ext_file = EXTENSIONS_DIR / f"{name}.py"
    ext_file.write_text(raw_code, encoding="utf-8")

    # 4. 动态执行注册
    try:
        exec_globals = {"ip": ipython}
        exec(compile(raw_code, str(ext_file), "exec"), exec_globals)
        success = True
        error = ""
    except Exception as e:
        success = False
        error = str(e)

    # 5. 写入历史
    history = _load_history()
    history.append({
        "name": name,
        "request": request,
        "file": str(ext_file),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "error": error,
    })
    _save_history(history)

    return {"name": name, "code": raw_code, "success": success, "error": error}


def load_all(ipython) -> list:
    """
    启动时恢复所有历史扩展（重新执行注册代码）。
    返回已加载的扩展名列表。
    """
    loaded = []
    for py_file in sorted(EXTENSIONS_DIR.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            code = py_file.read_text(encoding="utf-8")
            exec_globals = {"ip": ipython}
            exec(compile(code, str(py_file), "exec"), exec_globals)
            loaded.append(py_file.stem)
        except Exception:
            pass
    return loaded


def list_extensions() -> list:
    """返回所有已进化的扩展列表"""
    return _load_history()


def _infer_name(code: str, request: str) -> str:
    """从代码或请求中推断扩展名"""
    # 尝试从代码里找 register_magic_function(fn_name
    m = re.search(r"register_magic_function\((\w+)", code)
    if m:
        return m.group(1)

    # 尝试找 def (命令名)_magic 或 def magic_(名)
    m = re.search(r"def\s+(\w+)\s*\(", code)
    if m:
        return m.group(1).replace("_magic", "").replace("magic_", "")

    # 从请求中提取关键词
    words = re.findall(r"[a-zA-Z_]\w*|[\u4e00-\u9fff]+", request)
    for w in words:
        if re.match(r"[a-zA-Z_]\w+", w) and len(w) > 2:
            return w.lower()

    return f"ext_{len(list_extensions()) + 1}"
