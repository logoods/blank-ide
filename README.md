# Blank-IDE / world-platform

> **一个会自己生长的 IDE — LLM 就是操作系统**  
> **An IDE that grows itself — LLM as the Operating System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![OpenAI Compatible](https://img.shields.io/badge/LLM-OpenAI%20Compatible-green.svg)](https://platform.openai.com/docs/api-reference)

```
你说：给我加一个 %summarize 命令 / You say: add a %summarize command
   → LLM 生成 Python 魔法函数 / LLM generates a Python magic function
     → 写入 ide_extensions/ / Written to ide_extensions/
       → 立即出现在 Magic Terminal / Appears in Magic Terminal immediately
         → 点击运行，看到输出 / Click Run, see output
```

---

## 赛道定位 / Market Position

**传统 IDE** 靠插件扩展，靠发版迭代。**Copilot 类工具** 是 IDE 里的智能助手。  
**Traditional IDEs** grow through plugins and release cycles. **Copilot-style tools** are smart assistants inside the IDE.  
`world-platform` 走第三条路：**IDE 本身就是一个可被 LLM 重写的运行时**。  
`world-platform` takes a third path: **the IDE itself is a runtime that LLM can rewrite**.

| | 传统 IDE / Traditional IDE | Copilot / Cursor | world-platform |
|---|---|---|---|
| 扩展方式 / Extension | 手写插件 / Write plugins | 不可扩展 / Not extensible | **LLM 实时生成并注入 / LLM-generated, injected live** |
| 状态管理 / State | 无共享状态 / No shared state | 无 / None | **全局 World State（Pydantic）/ Global World State** |
| 工作流 / Workflow | 无 / None | 无 / None | **可视化节点白板 + 执行引擎 / Visual node canvas + engine** |
| 模型绑定 / Model | 无 / None | 强绑定单一提供商 / Locked to one vendor | **任意 OpenAI 兼容接口 / Any OpenAI-compatible endpoint** |
| 进化能力 / Evolution | 无 / None | 无 / None | **观察行为 → 自主生成新功能 / Observe → autonomously generate features** |

> 这不是"更好的代码补全"，而是**把 LLM 当作 IDE 的 OS 内核**——所有功能都是运行时产物，而非预装件。  
> This is not "better autocomplete". It treats the **LLM as the OS kernel of the IDE** — all features are runtime artifacts, not preinstalled binaries.

---

## 设计理念 / Design Philosophy

### LLM-First：

大多数 AI 工具把 LLM 当作"黑盒 API"——发一条消息，收一段字符串。  
`world-platform` 的做法：**LLM 的输入和输出都是结构化的领域对象**。

Most AI tools treat LLM as a "black-box API" — send a string, get a string.  
`world-platform` makes **both LLM input and output structured domain objects**:

```python
# LLM 的输入是序列化的 World State（不是拼接字符串）
# LLM input = serialized World State (not ad-hoc string concatenation)
prompt = schema.to_prompt()   # → "## World State\n- project: ...\n- phase: ..."

# LLM 的输出是经过验证的 Pydantic 对象（不是解析字符串）
# LLM output = validated Pydantic object (not parsed strings)
cmd: IDECommand = llm.complete_structured(prompt, IDECommand)
# cmd.action = "set_field"  cmd.target = "phase"  cmd.params = {"value": "v1"}
```

**结果**：LLM 永远在一个有上下文、有约束、可回滚的状态机里工作，而不是在无状态的聊天框里。  
**Result**: LLM always operates inside a stateful, constrained, rollback-able state machine — not a stateless chat box.

### 模型无关性：换模型不换代码 / Model-Agnostic by Design

`LLMClient` 统一封装所有 OpenAI 兼容接口，切换模型只需改配置：  
`LLMClient` wraps any OpenAI-compatible endpoint — switching models requires only config changes:

```python
# DeepSeek → OpenAI → 本地 Ollama，代码完全一致
# DeepSeek → OpenAI → local Ollama — identical code
llm = LLMClient(model="deepseek-chat",  base_url="https://api.deepseek.com/v1",  api_key="sk-...")
llm = LLMClient(model="gpt-4o",         base_url="https://api.openai.com/v1",     api_key="sk-...")
llm = LLMClient(model="llama3",          base_url="http://localhost:11434/v1",     api_key="none")
```

所有上层组件（Agent / Evolver / Magic / Workflow）对底层模型零感知。模型是**可插拔的算力单元**，不是架构的一部分。  
All upper-layer components are model-agnostic. Models are **pluggable compute units**, not architectural dependencies.

### 进化闭环：IDE 观察自己并改进自己 / The Self-Evolution Loop

```
观察 (Observer)  →  进化 (Evolver/LLM)  →  注入 (ide_extensions/)  →  执行 (Magic Terminal)
     ↑                                                                          |
     └──────────────────── 写入 World State ←──────────────────────────────────┘
```

每一次执行都是数据，数据驱动下一次进化。这是 IDE 的**增量自学习闭环**，不需要人工干预。  
Every execution is data; data drives the next evolution. This is the IDE's **incremental self-learning loop** — no human intervention required.

---

## 这是什么 / What is this?

`world-platform` 是一个 **AI 原生 IDE 的内核**，由三层组成：

1. **Web 白板画布** — 可视化节点编辑器，运行在浏览器，零配置
2. **自进化魔法命令系统** — LLM 实时生成并注入新命令，`%run_workflow`、`%evolve_node`……
3. **World State 中间件** — 所有节点、命令、执行结果共享同一个 Pydantic 状态图

`world-platform` is the **kernel** of an AI-native IDE, with three layers:

1. **Web Whiteboard Canvas** — visual node editor in the browser, zero config
2. **Self-evolving Magic Command System** — LLM generates and injects new commands live
3. **World State Middleware** — all nodes, commands, and results share one Pydantic state graph

---

## 快速理解 / Get the Idea in 2 Minutes

不想看文字？直接跑 Jupyter 演示，5 个 cell 走完核心概念：  
Skip the text — run the Jupyter demo. 5 cells cover all core concepts:

```bash
pip install -e . openai "pydantic>=2" jupyter
jupyter notebook examples/demo.ipynb
```

demo 覆盖：World State 读写 → LLM 结构化输出 → 魔法命令注入 → 进化闭环。  
The demo covers: World State read/write → LLM structured output → magic command injection → self-evolution loop.

> 想直接上手 Web IDE？跳到 [快速开始 / Quick Start](#快速开始--quick-start)。  
> Want to jump straight to the Web IDE? See [Quick Start](#快速开始--quick-start) below.

---

## 快速开始 / Quick Start

### 1. 安装 / Install

```bash
git clone https://github.com/YOUR_USERNAME/world-platform.git
cd world-platform
pip install -e .
pip install openai          # LLM 客户端 / LLM client
pip install "pydantic>=2"
```

### 2. 启动服务 / Start Services

开两个终端 / Open two terminals:

```bash
# 终端 1 — Python 进化引擎 / Terminal 1 — Python evolution engine
python web/pyserver.py

# 终端 2 — Web IDE / Terminal 2 — Web IDE
node web/server.js
```

打开浏览器：`http://localhost:3000`  
Open browser: `http://localhost:3000`

### 3. 配置大模型 / Configure LLM

点击右上角 **⚙ LLM** 按钮，填入：  
Click **⚙ LLM** in the top-right corner and fill in:

| 字段 / Field | DeepSeek 示例 / Example |
|---|---|
| Provider | DeepSeek |
| Base URL | `https://api.deepseek.com/v1` |
| Model | `deepseek-chat` |
| API Key | `sk-...` |

支持 DeepSeek / OpenAI / Claude / Qwen / Ollama 等任意 OpenAI 兼容接口。  
Supports DeepSeek / OpenAI / Claude / Qwen / Ollama and any OpenAI-compatible endpoint.

### 4. 玩法 / How to Play

**画布 / Canvas**
- 从左侧面板拖拽节点类型到画布，连线构建工作流  
  Drag node types from the left panel onto the canvas and connect them to build workflows
- 点击节点 → 右侧 Magic Terminal 自动填入节点名，可直接调用命令处理它  
  Click a node → the Magic Terminal on the right fills in the node name automatically

**进化 IDE / Evolve the IDE**
- 右侧面板 → **🧬 IDE Evolution** → 输入描述（或留空让 LLM 自主决定）→ 点 **✨ Evolve**  
  Right panel → **🧬 IDE Evolution** → type a description (or leave blank for LLM to decide) → click **✨ Evolve**
- 几秒后新命令出现在 **✨ Magic Commands** 列表，点击徽章填入命令名，按 **▶ Run Magic** 执行  
  Seconds later, the new command appears in **✨ Magic Commands**; click its badge to fill the name, then press **▶ Run Magic**

**魔法命令 / Magic Commands**
| 命令 / Command | 说明 / Description |
|---|---|
| `%hello` | 显示当前 World State / Show current World State |
| `%world` | 查看/写入 World State（`%world set key=val`）/ Read or write World State |
| `%run_workflow` | 用 LLM 串联执行白板上的所有节点 / Run all canvas nodes in sequence via LLM |
| `%json_import` | 粘贴 JSON 直接生成节点 / Paste JSON to generate nodes instantly |
| `%evolve_node <label>` | 让 LLM 对指定节点提出进化建议 / Ask LLM for evolution suggestions on a node |
| 你进化出来的 / Your evolved ones | 无限扩展 / Unlimited extensions |

**World State**
- 左侧面板实时显示状态键值  
  The left panel shows all state key-values in real time
- `%world set project=Blank-IDE` 写入后立即刷新  
  Run `%world set project=Blank-IDE` and the panel refreshes instantly

---

## 架构 / Architecture

```
world-platform/
├── agents/
│   ├── llm_client.py     # 统一 LLM 客户端（基于 openai 库）/ Unified LLM client (openai-based)
│   └── agent.py          # Agent: schema + trace + memory + middleware + planner
├── runtime/
│   ├── field.py          # Field    — 世界状态原子单元 / Atomic world state unit
│   ├── schema.py         # Schema   — 世界状态图 / World state map
│   ├── command.py        # IDECommand — LLM 结构化输出协议 / Structured LLM output protocol
│   ├── cell.py           # LLMCell  — 单次 LLM 执行单元 / Single LLM execution unit
│   ├── workflow.py       # Workflow — 顺序 Cell 执行器 / Sequential cell runner
│   ├── magic.py          # Blank IDE 魔法命令系统 / Magic command system
│   ├── observer.py       # Observer — 执行事件监听 / Execution event monitor
│   ├── evolver.py        # Evolver  — IDE 自主进化引擎 / IDE self-evolution engine
│   ├── ide_evolution.py  # 扩展生成与持久化 / Extension generator & persistence
│   └── ide_extensions/   # 进化出的魔法命令（git ignored）/ Evolved magic commands
├── kernel/
│   └── kernel.py         # WorldKernel — 统一内核 + 快照回滚 / Unified kernel + snapshot/restore
├── web/
│   ├── server.js         # Node.js 静态服务 + 代理 / Static server + proxy
│   ├── pyserver.py       # Python HTTP 桥接服务 / Python HTTP bridge
│   ├── index.html        # Web IDE 主界面 / Web IDE main UI
│   └── js/               # 前端逻辑 / Frontend logic
└── examples/
    └── demo.ipynb        # Jupyter 演示 / Jupyter demo
```

---

## 核心设计 / Core Design

### World State — Schema + Field

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

### LLM 结构化输出 / Structured Output — IDECommand

```python
from agents.llm_client import LLMClient
from runtime.command import IDECommand

llm = LLMClient(model="deepseek-chat", api_key="sk-...", base_url="https://api.deepseek.com/v1")
cmd = llm.complete_structured(
    prompt=f"{schema.to_prompt()}\nWhat should the IDE do next?",
    model_class=IDECommand,
)
print(cmd.action)   # "set_field"
```

### 自我进化 / Self-Evolving IDE

```python
# Jupyter 中 / In Jupyter:
%load_ext runtime.magic

%%ide
Add a %schema_table command that renders world state as a Markdown table
# → 立即注入，立即可用 / Injected and usable immediately
```

### Pipeline — 链式多步推理 / Chainable Multi-Step Reasoning

```python
from kernel import Pipeline

result = (
    Pipeline(api_key="sk-...", model="deepseek-chat")
    .step("Extract top 3 challenges from: {{input}}")
    .step("Propose a solution for each: {{input}}")
    .step("Label each P0/P1/P2: {{input}}")
    .run_final("Build an AI-native IDE runtime.")
)
```

---

## 支持的 LLM / Supported LLMs

| 提供商 / Provider | 模型示例 / Model example | Base URL |
|---|---|---|
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com/v1` |
| OpenAI   | `gpt-4o` | `https://api.openai.com/v1` |
| Qwen     | `qwen-plus` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Claude   | `claude-3-5-sonnet` | `https://api.anthropic.com/v1` |
| Ollama   | `llama3` | `http://localhost:11434/v1` |

---

## 路线图 / Roadmap

### 已完成 / Done

- [x] World Middleware Runtime（Field / Schema / Workflow / Cell / Trace）
- [x] 统一 LLM 客户端（openai 库，兼容所有 OpenAI 接口）/ Unified LLM client
- [x] IDECommand — LLM 原生 IDE 指令协议 / LLM-native instruction protocol
- [x] Planner、Middleware、Memory、Multi-Agent、WorldKernel、Pipeline
- [x] Blank IDE 魔法命令系统（Jupyter）/ Magic command system in Jupyter
- [x] Observer + Evolver — IDE 自主进化引擎 / Self-evolution engine
- [x] **Web IDE 白板画布 v0.1** — 可视化节点编辑器 / Visual node editor
- [x] **Web IDE 自进化闭环 v0.2** — 浏览器直接触发 LLM 进化 / Browser-triggered evolution
- [x] **Magic Terminal v0.3** — 进化出的命令可在浏览器直接执行 / Evolved commands executable in browser
- [x] **World State 实时同步 v0.4** — Canvas / Magic / Python 三端共享同一状态 / Shared state across canvas, magic, Python

### 计划中 / Planned

- [ ] **World State 持久化** — 重启后恢复状态，支持 JSON / SQLite 后端  
      Persist world state across restarts (JSON / SQLite backend)
- [ ] **Workflow 可视化执行** — 白板节点逐步高亮，实时看到数据流向  
      Visual workflow execution with step-by-step node highlighting
- [ ] **多模型并行 Cell** — 同一节点同时跑多个模型，对比结果  
      Parallel multi-model cells — run multiple models on same node, compare results
- [ ] **Agent Store** — 一键安装社区进化出的魔法包  
      One-click install of community-evolved magic packs
- [ ] **Jupyter ↔ Web 双向同步** — 在 Jupyter 进化的命令自动同步到 Web，反之亦然  
      Bidirectional sync between Jupyter and Web IDE
- [ ] **IDE 进化记忆** — 记录哪些进化有用，下次自动复用模式  
      Evolution memory — track which evolutions worked, reuse patterns automatically

---

## License

MIT
