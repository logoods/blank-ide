import json
import re
from typing import Generator, Optional, Type, TypeVar
from pydantic import BaseModel
from openai import OpenAI

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """
    统一大模型接口（基于 openai 库，兼容 DeepSeek / GPT / Qwen / 本地模型）。
    base_url 只需填到 /v1，openai 库自动拼 /chat/completions。
    """

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        raw = (base_url or "https://api.deepseek.com/v1").rstrip("/")
        for suffix in ("/chat/completions", "/completions"):
            if raw.endswith(suffix):
                raw = raw[: -len(suffix)]
                break
        self.base_url = raw
        self._client = OpenAI(
            api_key=api_key or "none",
            base_url=self.base_url,
            timeout=60.0,       # 连接 + 读取总超时 60s
            max_retries=1,
        )

    # -------------------------
    # 非流式调用
    # -------------------------
    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=False,
        )
        return resp.choices[0].message.content

    # -------------------------
    # 流式调用
    # -------------------------
    def stream(self, prompt: str, temperature: float = 0.7) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    # -------------------------------------------------------
    # 结构化输出：LLM 返回 Pydantic 模型实例
    # -------------------------------------------------------
    def complete_structured(
        self,
        prompt: str,
        model_class: Type[T],
        temperature: float = 0.2,
    ) -> T:
        """
        让 LLM 返回符合 Pydantic Schema 的 JSON，自动解析为模型实例。

        用法：
            cmd = llm.complete_structured(prompt, IDECommand)
            batch = llm.complete_structured(prompt, IDECommandBatch)
        """
        schema_str = json.dumps(
            model_class.model_json_schema(), ensure_ascii=False, indent=2
        )
        full_prompt = (
            f"{prompt}\n\n"
            f"You MUST return a valid JSON object matching this schema (no markdown, no explanation):\n"
            f"{schema_str}"
        )

        raw = self.complete(full_prompt, temperature=temperature)

        # 提取 JSON（兼容 LLM 偶尔包裹 ```json ... ```）
        raw = raw.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if match:
            raw = match.group(1).strip()

        return model_class.model_validate_json(raw)
