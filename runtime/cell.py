from pydantic import BaseModel
from agents.llm_client import LLMClient


class LLMCell(BaseModel):
    """
    单次 LLM 调用的执行单元 / Single LLM call execution unit.
    是 Workflow 的基本构成块。/ Basic building block of a Workflow.
    """

    prompt: str                     # 发送给 LLM 的提示 / Prompt sent to LLM
    model: str = "deepseek-chat"   # 使用的模型 / Model to use
    api_key: str = None             # API 密钥 / API key

    def run(self) -> str:
        """执行 LLM 调用并返回结果 / Execute LLM call and return result."""
        llm = LLMClient(
            model=self.model,
            api_key=self.api_key
        )
        return llm.complete(self.prompt)
