from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.agent import Agent


class AgentHub:
    """
    多 Agent 协作中心 / Multi-Agent collaboration hub.
    - register(agent)       注册 Agent           / Register an agent
    - send(from, to, msg)   点对点发消息          / Send point-to-point message
    - broadcast(from, msg)  广播给所有其他 Agent  / Broadcast to all other agents
    """

    def __init__(self):
        self.agents: Dict[str, "Agent"] = {}

    def register(self, agent: "Agent") -> None:
        self.agents[agent.name] = agent

    def send(self, from_name: str, to_name: str, message: dict) -> None:
        target = self.agents.get(to_name)
        if target is None:
            raise ValueError(f"Agent '{to_name}' not registered in AgentHub")
        target.receive(from_name, message)

    def broadcast(self, from_name: str, message: dict) -> None:
        for name, agent in self.agents.items():
            if name != from_name:
                agent.receive(from_name, message)

    def list_agents(self) -> list:
        return list(self.agents.keys())
