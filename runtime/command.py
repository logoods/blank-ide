"""
IDECommand — 大模型返回的结构化 IDE 指令（Pydantic 结构化输出）
IDECommand — Structured IDE instruction returned by LLM (Pydantic structured output)

调用链 / Call chain:
    IDE → Agent → LLM → IDECommand → IDE 执行 / IDE executes

支持的 action / Supported actions:
    set_field       写入世界状态       / Write world state
    run_workflow    执行 Workflow      / Execute Workflow
    create_cell     创建新 Cell        / Create new Cell
    run_cell        执行某个 Cell      / Execute a Cell
    show_panel      展示 UI 面板       / Show UI panel
    log             记录日志           / Log a message
    plan            规划步骤           / Plan steps
    custom          自定义动作（扩展） / Custom action (extensible)
"""

from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


ActionType = Literal[
    "set_field",
    "run_workflow",
    "create_cell",
    "run_cell",
    "show_panel",
    "log",
    "plan",
    "custom",
]


class IDECommand(BaseModel):
    """大模型返回的结构化 IDE 指令。
    Structured IDE instruction returned by LLM."""

    action: ActionType = Field(description="要执行的 IDE 动作类型 / IDE action type to execute")
    target: Optional[str] = Field(None, description="动作目标（字段名 / Cell 名 / 面板名）/ Action target (field/cell/panel name)")
    params: dict[str, Any] = Field(default_factory=dict, description="动作参数 / Action parameters")
    description: str = Field(default="", description="本条指令的说明，供 Trace 记录 / Instruction description for Trace")

    def summary(self) -> str:
        return f"[{self.action}] {self.target or ''} — {self.description}"


class IDECommandBatch(BaseModel):
    """多条 IDECommand 的批次，大模型可一次返回多步指令。
    A batch of IDECommands; LLM can return multiple steps at once."""

    commands: list[IDECommand] = Field(default_factory=list)  # 指令列表 / Command list
    goal: str = Field(default="", description="本批次的总目标 / Overall goal for this batch")

    def __iter__(self):
        return iter(self.commands)

    def __len__(self):
        return len(self.commands)
