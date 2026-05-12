import requests
import json
import re
from typing import Generator, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """
    统一大模型接口：
    - DeepSeek
    - GPT
    - Qwen
    - Claude
    - 本地模型（vLLM / LM Studio / Ollama）
    """

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model

        # 默认 DeepSeek
        self.base_url = base_url or "https://api.deepseek.com"
        self.api_key = api_key or ""

    # -------------------------
    # 非流式调用
    # -------------------------
    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": False,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        resp = requests.post(url, headers=headers, data=json.dumps(payload))
        resp.raise_for_status()

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # -------------------------
    # 流式调用
    # -------------------------
    def stream(self, prompt: str, temperature: float = 0.7) -> Generator[str, None, None]:
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": True,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        with requests.post(url, headers=headers, data=json.dumps(payload), stream=True) as resp:
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith(b"data: "):
                    chunk = line[len(b"data: "):].decode("utf-8")
                    if chunk == "[DONE]":
                        break
                    data = json.loads(chunk)
                    delta = data["choices"][0]["delta"].get("content", "")
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
