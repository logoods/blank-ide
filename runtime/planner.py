import json
import re
from typing import Optional
from agents.llm_client import LLMClient


class Planner:
    """
    使用 LLM 自动规划下一步任务列表。/ Use LLM to auto-plan the next task list.
    plan(goal, context) -> list[str]
    """

    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.llm = LLMClient(model=model, api_key=api_key, base_url=base_url)

    def plan(self, goal: str, context: dict = None) -> list[str]:
        """
        给定目标和上下文，返回步骤列表（字符串数组）。
        Given a goal and context, return a list of step descriptions.
        """
        prompt = (
            "You are a planning agent. Given the goal and context, "
            "return a JSON array of step descriptions to achieve the goal.\n\n"
            f"Goal: {goal}\n"
            f"Context: {json.dumps(context or {}, ensure_ascii=False)}\n\n"
            'Return ONLY a JSON array, e.g. ["step 1", "step 2", ...]'
        )
        raw = self.llm.complete(prompt)

        # 尝试直接解析 JSON / Try direct JSON parse
        try:
            steps = json.loads(raw)
            if isinstance(steps, list):
                return steps
        except json.JSONDecodeError:
            pass

        # 从返回文本中提取 JSON 数组 / Extract JSON array from text
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 降级：整段文本作为单步 / Fallback: treat entire text as single step
        return [raw.strip()]
