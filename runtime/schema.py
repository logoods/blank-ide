import json
from pydantic import BaseModel
from typing import Dict, Any
from runtime.field import Field


class Schema(BaseModel):
    fields: Dict[str, Field] = {}

    def get(self, name: str):
        return self.fields.get(name)

    def set(self, name: str, value: Any):
        self.fields[name] = Field(name=name, value=value)

    # -------------------------------------------------------
    # LLM-native：将 Schema 序列化为 LLM 可读的上下文 prompt
    # Serialize Schema into LLM-readable context prompt
    # -------------------------------------------------------
    def to_prompt(self) -> str:
        """
        把当前世界状态转成自然语言，注入到 LLM prompt 里。
        Serialize current world state into natural language for LLM context injection.

        示例输出 / Example output:
            ## World State
            - user_name (str): Alice
            - counter (int): 42
        """
        if not self.fields:
            return "## World State\n(empty)"

        lines = ["## World State"]
        for name, field in self.fields.items():
            lines.append(f"- {name} ({field.type}): {field.value}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """返回 {name: value} 简洁字典，方便传给 LLM context。
        Return a flat {name: value} dict for LLM context injection."""
        return {name: f.value for name, f in self.fields.items()}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    # -------------------------------------------------------
    # 从 LLM 结构化输出（dict）批量更新 Schema
    # Batch-update Schema from LLM structured output (dict)
    # -------------------------------------------------------
    def from_llm(self, data: dict) -> None:
        """
        大模型返回一个 dict，批量写入 Schema。
        Batch-write a dict returned by LLM into Schema.
        data = {"user_name": "Bob", "step": 3}
        """
        for name, value in data.items():
            self.set(name, value)
