# world-platform

> **AINative Blank IDE + World Middleware Runtime**
>
> 一个 LLM 原生的 AI 运行时框架 — 在 Jupyter 或 Web IDE 中构建任意 AI 系统，  
> 以结构化 Pydantic 模型和 DeepSeek/GPT/Claude 驱动。  
>
> A LLM-native AI Runtime framework — build any AI system inside Jupyter or a Web IDE,  
> powered by structured Pydantic models and DeepSeek / GPT / Claude.

---

## 这是什么 / What is this?

`world-platform` 是一个 **AI 原生 IDE 的内核**。  
它不需要手写功能——IDE 通过 LLM 生成的 `IDECommand` 对象自我进化。

`world-platform` is the **kernel** of an AI-native IDE.  
Instead of writing features by hand, the IDE grows itself via LLM-generated `IDECommand` objects.

```
用户输入 / User prompt
  → Agent (LLM)
    → IDECommand (Pydantic 结构化输出 / structured output)
      → IDE 执行 / IDE executes:
          set_field · run_workflow · create_cell · show_panel · plan …
```

---

## 架构 / Architecture

```
world-platform/
├── agents/
│   ├── llm_client.py     # 统一 LLM 客户端 / Unified LLM client (DeepSeek/GPT/Claude/local)
│   └── agent.py          # Agent: schema + trace + memory + middleware + planner
├── runtime/
│   ├── field.py          # Field    — 世界状态原子单元 / Atomic world state unit (Pydantic)
│   ├── schema.py         # Schema   — 世界状态图 + LLM 上下文序列化 / World state map + LLM context
│   ├── command.py        # IDECommand — LLM 结构化输出协议 / Structured LLM output protocol
│   ├── cell.py           # LLMCell  — 单次 LLM 执行单元 / Single LLM execution unit
│   ├── workflow.py       # Workflow — 顺序 Cell 执行器 / Sequential cell runner
│   ├── trace.py          # Trace    — 事件审计日志 / Event audit log
│   ├── worlddb.py        # WorldDB  — 内存 KV 存储 / In-memory KV store
│   ├── planner.py        # Planner  — LLM 自动规划 / LLM auto-planning
│   ├── middleware.py     # Middleware — before/after hooks
│   ├── memory.py         # Memory   — 长期记忆 + JSON 持久化 / Long-term memory + JSON persistence
│   ├── multiagent.py     # AgentHub — 多 Agent 消息路由 / Multi-agent message routing
│   ├── magic.py          # Blank IDE 魔法命令系统 / Magic command system (%%world / %%dev / %%ide)
│   ├── observer.py       # Observer — 被动监听执行事件 / Passive execution event monitor
│   ├── evolver.py        # Evolver  — IDE 自主进化引擎 / IDE self-evolution engine
│   └── ide_evolution.py  # %%ide 扩展生成与持久化 / %%ide extension generator & persistence
├── kernel/
│   ├── kernel.py         # WorldKernel — 统一内核 / Unified kernel
│   └── __init__.py       # Pipeline   — 链式多步 LLM 流水线 / Chainable multi-step LLM pipeline
└── examples/
    └── demo.ipynb        # Jupyter 演示 / Jupyter demo notebook
```

---

## 核心设计 / Core Design: Schema + Pydantic as LLM-native Protocol

### 1. 世界状态 / World State — Schema + Field

每条状态都是带类型的 `Field`，`Schema` 自动序列化为 LLM 可读上下文。  
Every piece of state is a typed `Field`; `Schema` auto-serializes to LLM-readable context.

```python
from runtime.schema import Schema

schema = Schema()
schema.set("project", "world-platform")
schema.set("phase", "prototype")

print(schema.to_prompt())
# ## World State
# - project (str): world-platform
# - phase (str): prototype
```

### 2. LLM 结构化输出 / Structured LLM Output — IDECommand

LLM 返回经过验证的 Pydantic 对象，无字符串解析，无幻觉。  
LLM returns a validated Pydantic object — no string parsing, no hallucination.

```python
from agents.llm_client import LLMClient
from runtime.command import IDECommand

llm = LLMClient(model="deepseek-chat", api_key="sk-...")

cmd = llm.complete_structured(
    prompt=f"{schema.to_prompt()}\nWhat should the IDE do next?",
    model_class=IDECommand,
)
print(cmd.action)   # "set_field"
print(cmd.target)   # "phase"
print(cmd.params)   # {"value": "in-development"}
```

### 3. Blank IDE 魔法命令 / Blank IDE Magic Commands — Jupyter

```python
%load_ext runtime.magic

# 用自然语言写世界状态 / Write world state in natural language
%%world
Project is world-platform, phase is prototype, owner is Alice, priority high.

# 白板模式：LLM 决策并自动执行 / Whiteboard: LLM decides and executes
%%dev --exec
Update phase to in-development and mark missing module as kernel_scheduler

# 自动规划步骤 / Auto-plan steps
%%dev --plan
Complete the kernel_scheduler module development
```

### 4. WorldKernel — 统一内核 / Unified Kernel

```python
from kernel import WorldKernel

k = WorldKernel(api_key="sk-...", model="deepseek-chat")
k.set("project", "world-platform")
k.set("phase", "prototype")

k.snapshot("v1")              # 保存快照 / Save snapshot
k.set("phase", "experimental")
k.restore("v1")               # 一键回滚 / Roll back in one call

steps = k.plan("Build the kernel scheduler module")
print(k.state())              # 打印世界状态摘要 / Print state summary
```

### 5. Pipeline — 链式多步 LLM 推理 / Chainable Multi-Step LLM Reasoning

```python
from kernel import Pipeline

result = (
    Pipeline(api_key="sk-...", model="deepseek-chat")
    .step("Extract top 3 technical challenges from: {{input}}")
    .step("Propose a solution for each challenge: {{input}}")
    .step("Label each solution P0/P1/P2 by urgency: {{input}}")
    .run_final("Build an AINative IDE runtime framework with LLM integration.")
)
print(result)
```

### 6. 自我进化 / Self-Evolving IDE

```python
# IDE 观察你的使用行为，自主设计并注入新功能
# IDE observes your behavior, autonomously designs and injects new capabilities

%ide_observe   # 查看执行日志 / View execution log
%ide_evolve    # 触发一次进化 / Trigger one evolution cycle
%ide_history   # 查看进化历史 / View evolution history

# 用自然语言描述新功能，立即注入 / Describe new capability in NL, inject immediately
%%ide
Add a %schema_table command that renders world state as a Markdown table
```

### 7. 多 Agent 协作 / Multi-Agent

```python
from agents.agent import Agent
from runtime.multiagent import AgentHub

hub = AgentHub()
alice = Agent(name="alice", api_key="sk-...")
bob   = Agent(name="bob",   api_key="sk-...")
hub.register(alice)
hub.register(bob)
hub.send("alice", "bob", {"task": "run workflow A"})
hub.broadcast("alice", {"status": "ready"})
```

---

## 快速开始 / Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/world-platform.git
cd world-platform
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -e .
```

在 Jupyter 中打开 `examples/demo.ipynb`，修改 `API_KEY` 后顺序运行所有单元格。  
Open `examples/demo.ipynb` in Jupyter, set your `API_KEY`, then run all cells in order.

---

## 支持的 LLM / Supported LLMs

| 提供商 / Provider | 模型示例 / Model example |
|------------------|------------------------|
| DeepSeek | `deepseek-chat`, `deepseek-v4-flash` |
| OpenAI   | `gpt-4o`, `gpt-4-turbo` |
| Qwen     | `qwen-plus` |
| Claude   | `claude-3-5-sonnet` |
| 本地 / Local | vLLM / LM Studio / Ollama（设置 `base_url` / set `base_url`）|

---

## 路线图 / Roadmap

- [x] World Middleware Runtime（Field / Schema / Workflow / Cell / Trace / WorldDB）
- [x] 统一 LLM 客户端 + 结构化输出 / Unified LLM client + `complete_structured`
- [x] IDECommand — LLM 原生 IDE 指令协议 / LLM-native IDE instruction protocol
- [x] Planner — LLM 自动规划 / LLM auto-planning
- [x] Middleware — before/after hooks
- [x] Memory — 长期记忆 + JSON 持久化 / Long-term memory with JSON persistence
- [x] Multi-Agent — AgentHub 消息路由 / AgentHub message routing
- [x] Blank IDE 魔法命令 / Magic commands（`%%world` / `%%dev` / `%%ide`）
- [x] Observer — 被动执行监听 / Passive execution monitoring
- [x] Evolver — IDE 自主进化引擎 / IDE self-evolution engine
- [x] WorldKernel — 统一内核 + 快照回滚 / Unified kernel + snapshot/restore
- [x] Pipeline — 链式多步 LLM 流水线 / Chainable multi-step LLM pipeline
- [ ] World Kernel 调度器 / Scheduler
- [ ] Web IDE — Blank IDE 前端 / Frontend
- [ ] Agent Store
- [ ] Workflow 可视化 / Workflow visualizer

---

## License

MIT
