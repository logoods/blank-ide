from typing import Optional
from runtime.field import Field
from runtime.schema import Schema
from runtime.workflow import Workflow
from runtime.trace import Trace
from runtime.worlddb import WorldDB
from runtime.middleware import Middleware
from runtime.memory import Memory
from runtime.planner import Planner


class Agent:
    def __init__(
        self,
        name: str = "agent",
        memory_path: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.name = name
        self.schema = Schema(fields={})
        self.trace = Trace()
        self.db = WorldDB()
        self.middleware = Middleware()
        self.memory = Memory(path=memory_path)
        self.planner = Planner(api_key=api_key, base_url=base_url)

    # 写入世界状态
    def set(self, key, value):
        self.schema.set(key, value)
        self.trace.log("set", {key: value})

    # 读取世界状态
    def get(self, key):
        return self.schema.get(key)

    # 执行能力（Cell）
    def run_cell(self, cell):
        ctx = {"cell": cell}
        self.middleware.run_before(ctx)
        self.trace.log("cell_start", cell.model_dump())
        result = cell.run()
        self.trace.log("cell_end", result)
        self.middleware.run_after(ctx, result)
        return result


    # 存储
    def save(self, key, value):
        self.db.save(key, value)

    def load(self, key):
        return self.db.load(key)

    def run_workflow(self, workflow):
        ctx = {"workflow": workflow}
        self.middleware.run_before(ctx)
        self.trace.log("workflow_start")
        result = workflow.run()
        self.trace.log("workflow_end", result)
        self.middleware.run_after(ctx, result)
        return result

    # 自动规划
    def plan(self, goal: str, context: dict = None) -> list:
        steps = self.planner.plan(goal, context)
        self.trace.log("plan", {"goal": goal, "steps": steps})
        return steps

    # 接收其他 Agent 的消息（Multi-Agent）
    def receive(self, from_name: str, message: dict) -> None:
        self.trace.log("receive", {"from": from_name, "message": message})
        self.memory.remember(f"msg_from_{from_name}", message, tags=["message"])
