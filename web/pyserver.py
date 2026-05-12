"""
Evolution Bridge Server — world-platform IDE 自进化 Python HTTP 服务

在 web/server.js 之外独立运行（默认端口 3001）。
server.js 通过反向代理把 /api/evolve/* 请求转发到此处。

启动:
    cd web
    python pyserver.py
    # 或带环境变量:
    DEEPSEEK_API_KEY=sk-... DEEPSEEK_MODEL=deepseek-chat python pyserver.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# --- 把项目根目录加入 sys.path，使 runtime/agents 可导入 ----
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PORT = int(os.environ.get("PY_PORT", 3001))
MAX_BODY = 1 * 1024 * 1024  # 1 MB


# ── 全局共享的"虚拟 IPython"上下文 ─────────────────────────

class _HeadlessIPython:
    """
    模拟 IPython shell。
    - register_magic_function 真正存储可调用函数
    - run_line_magic / run_cell_magic 可执行已注册命令
    - user_ns 共享命名空间（extensions 之间可传递变量）
    """

    def __init__(self) -> None:
        self.user_ns: dict[str, Any] = {}
        self._line_magics: dict[str, Any] = {}   # name → fn(line)
        self._cell_magics: dict[str, Any] = {}   # name → fn(line, cell)

    def register_magic_function(self, fn: Any, magic_kind: str = "line") -> None:
        name = getattr(fn, "__name__", str(fn))
        if magic_kind == "cell":
            self._cell_magics[name] = fn
        else:
            self._line_magics[name] = fn

    def register_magics(self, cls: Any) -> None:
        """IPython @magics_class 风格：扫描方法上的 magic 装饰器（简化）"""
        for attr in dir(cls):
            fn = getattr(cls, attr, None)
            if callable(fn) and getattr(fn, "magic_kind", None) in ("line", "cell"):
                self.register_magic_function(fn, fn.magic_kind)

    def run_line_magic(self, name: str, line: str) -> Any:
        fn = self._line_magics.get(name)
        if fn is None:
            raise KeyError(f"No line magic %{name} registered")
        return fn(line)

    def run_cell_magic(self, name: str, line: str, cell: str) -> Any:
        fn = self._cell_magics.get(name)
        if fn is None:
            raise KeyError(f"No cell magic %%{name} registered")
        return fn(line, cell)

    @property
    def magics(self) -> dict[str, list[str]]:
        return {
            "line": sorted(self._line_magics.keys()),
            "cell": sorted(self._cell_magics.keys()),
        }


_ip = _HeadlessIPython()

# ── 启动时加载所有历史扩展 ─────────────────────────────────────────────────
def _bootstrap_extensions() -> None:
    from pathlib import Path
    ext_dir = Path(__file__).parent.parent / "runtime" / "ide_extensions"
    for py_file in sorted(ext_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            code = py_file.read_text(encoding="utf-8")
            exec(compile(code, str(py_file), "exec"), {"ip": _ip})
        except Exception as exc:
            print(f"[pyserver] Skipped extension {py_file.name}: {exc}")

# ── Observer（全局单例，记录 Web 端发来的执行事件）────────────
from runtime.observer import Observer as _ObserverCls

class _WebObserver:
    """
    Web 端 Observer：不依赖 IPython events，由 /api/observe POST 主动写入日志。
    接口兼容 Observer.summary() / Observer.log。
    """

    def __init__(self, max_entries: int = 100) -> None:
        self.max_entries = max_entries
        self.log: list[dict] = []

    def record(self, entry: dict) -> None:
        self.log.append(entry)
        if len(self.log) > self.max_entries:
            self.log.pop(0)

    def summary(self, n: int = 15) -> str:
        recent = self.log[-n:]
        if not recent:
            return "(no observations yet)"
        lines = []
        for e in recent:
            status = "✓" if e.get("success", True) else "✗ ERROR"
            preview = str(e.get("cell", e.get("action", ""))).strip()[:120].replace("\n", " ↵ ")
            err = f" → {e['error']}" if e.get("error") else ""
            lines.append(f"{status}  {preview}{err}")
        return "\n".join(lines)


_observer = _WebObserver()

# ── Schema（全局世界状态）───────────────────────────────────
from runtime.schema import Schema as _Schema

_schema = _Schema()


# ── LLM 客户端 ──────────────────────────────────────────────
from agents.llm_client import LLMClient as _LLMClient

# ── 全局 LLM 配置（可通过 API 动态替换）──────────────────────────
_llm_config: dict[str, str] = {
    "model":    os.environ.get("DEEPSEEK_MODEL",    "deepseek-chat"),
    "api_key":  os.environ.get("DEEPSEEK_API_KEY",  ""),
    "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
}


def _get_llm() -> _LLMClient:
    return _LLMClient(
        model=_llm_config["model"],
        api_key=_llm_config["api_key"],
        base_url=_llm_config["base_url"],
    )


# ── 路由处理 ─────────────────────────────────────────────────
def _handle_observe(body: dict) -> dict:
    """记录一条 Web 端执行事件 → Observer 日志"""
    _observer.record(body)
    return {"ok": True, "total": len(_observer.log)}


def _handle_evolve(body: dict) -> dict:
    """
    触发一次进化：
    - 读取 Observer 日志摘要
    - 读取当前 Schema 世界状态
    - 调 ide_evolution.evolve() 生成新魔法命令
    - 返回进化结果
    """
    from runtime import ide_evolution

    world_context = _schema.to_prompt()
    request = body.get("request", "根据当前使用模式，自主设计并添加一个最有价值的 IDE 新功能")

    result = ide_evolution.evolve(
        request=request,
        world_context=f"{world_context}\n\n【行为摘要 / Behavior Summary】\n{_observer.summary(20)}",
        ipython=_ip,
        llm=_get_llm(),   # 使用界面配置的 LLM
    )
    return result


def _handle_evolve_list(_body: dict) -> dict:
    """返回所有已进化的扩展历史"""
    from runtime import ide_evolution

    return {"extensions": ide_evolution.list_extensions()}


def _handle_world_state(_body: dict) -> dict:
    """返回当前世界状态 JSON"""
    return {"state": _schema.to_dict()}


def _handle_world_set(body: dict) -> dict:
    """批量更新世界状态: {key: value, ...}"""
    for k, v in body.items():
        _schema.set(k, v)
    return {"ok": True, "state": _schema.to_dict()}


def _handle_config_get(_body: dict) -> dict:
    """返回当前 LLM 配置（隐藏 api_key 后几位）"""
    masked = "*" * max(0, len(_llm_config["api_key"]) - 4) + _llm_config["api_key"][-4:] if _llm_config["api_key"] else ""
    return {
        "model":    _llm_config["model"],
        "base_url": _llm_config["base_url"],
        "api_key":  masked,
    }


def _handle_config_set(body: dict) -> dict:
    """更新 LLM 配置并立即生效"""
    if "model" in body and body["model"]:
        _llm_config["model"] = str(body["model"])
    if "apiKey" in body and body["apiKey"]:
        _llm_config["api_key"] = str(body["apiKey"])
    if "baseUrl" in body and body["baseUrl"]:
        _llm_config["base_url"] = str(body["baseUrl"])
    return {"ok": True, "model": _llm_config["model"], "base_url": _llm_config["base_url"]}


def _handle_magic_list(_body: dict) -> dict:
    """返回已注册的所有魔法命令"""
    return {"magics": _ip.magics}


def _handle_magic_run(body: dict) -> dict:
    """
    执行一条魔法命令并捕获输出。
    body: {"name": "run_workflow", "line": "--list", "cell": ""}  (cell 可省)
    """
    import io, contextlib

    name = body.get("name", "").strip()
    line = body.get("line", "").strip()
    cell = body.get("cell", None)

    if not name:
        return {"ok": False, "error": "name is required", "output": ""}

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            if cell is not None:
                result = _ip.run_cell_magic(name, line, cell)
            else:
                result = _ip.run_line_magic(name, line)
        output = buf.getvalue()
        # 若函数用 return 而非 print，把返回值也展示出来
        if result is not None and str(result).strip():
            output = (output + str(result)).strip()
        return {"ok": True, "output": output or "(done)"}
    except KeyError as e:
        return {"ok": False, "error": str(e), "output": buf.getvalue()}
    except Exception as e:
        import traceback
        return {"ok": False, "error": str(e), "output": buf.getvalue() + "\n" + traceback.format_exc()}


# ── HTTP Handler ─────────────────────────────────────────────
_ROUTES: dict[str, dict[str, Any]] = {
    "POST /api/observe":        _handle_observe,
    "POST /api/evolve":         _handle_evolve,
    "GET /api/evolve/list":     _handle_evolve_list,
    "GET /api/world":           _handle_world_state,
    "POST /api/world":          _handle_world_set,
    "GET /api/config":          _handle_config_get,
    "POST /api/config":         _handle_config_set,
    "GET /api/magic":           _handle_magic_list,
    "POST /api/magic/run":      _handle_magic_run,
}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:  # suppress default logging
        pass

    def _send_json(self, status: int, body: Any) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        if length > MAX_BODY:
            raise ValueError("Payload too large")
        return json.loads(self.rfile.read(length))

    def _dispatch(self, method: str) -> None:
        from urllib.parse import urlparse
        path = urlparse(self.path).path
        key = f"{method} {path}"
        handler = _ROUTES.get(key)
        if handler is None:
            self._send_json(404, {"error": "Not found"})
            return
        try:
            body = self._read_body() if method in ("POST", "PUT") else {}
            result = handler(body)
            self._send_json(200, result)
        except Exception as exc:
            traceback.print_exc()
            self._send_json(500, {"error": str(exc)})

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


if __name__ == "__main__":
    # 让所有扩展里的 _get_world() 共用同一个 Schema 实例
    import runtime.magic as _magic_mod
    _magic_mod._world_schema = _schema

    _bootstrap_extensions()
    server = HTTPServer(("127.0.0.1", PORT), _Handler)
    print(f"[pyserver] Evolution API running on http://127.0.0.1:{PORT}")
    print(f"[pyserver] Project root: {ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[pyserver] Stopped.")
