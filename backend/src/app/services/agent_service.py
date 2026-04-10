from __future__ import annotations

from app.models.enums import AgentRole, AuditAction, ActorType
from app.repositories.agent_repository import AgentRepository
from app.repositories.stats_repository import StatsRepository
from app.services.audit_service import AuditService


class AgentService:
    def __init__(
        self,
        repository: AgentRepository,
        stats_repository: StatsRepository,
        audit_service: AuditService,
    ):
        self.repository = repository
        self.stats_repository = stats_repository
        self.audit_service = audit_service

    async def list_agents(self, from_at=None, to_at=None) -> list[dict]:
        agents = await self.repository.list_agents()
        stats_map: dict[str, dict] = {}
        if from_at and to_at:
            for row in await self.stats_repository.agents(from_at, to_at):
                stats_map[row["id"]] = row
        for agent in agents:
            stat = stats_map.get(agent["id"], {})
            agent["handled_tickets"] = stat.get("handled_tickets", 0)
            agent["avg_first_response_seconds"] = stat.get("avg_first_response_seconds")
            agent["closure_count"] = stat.get("closure_count", 0)
        return agents

    async def find_agent(self, username: str | None, chat_id: int | None) -> dict | None:
        return await self.repository.find_agent(username=username, chat_id=chat_id)

    async def create_agent(self, payload: dict, actor_id: str | None = None) -> dict:
        agent = await self.repository.create_agent(payload)
        await self.audit_service.log(
            actor_type=ActorType.SYSTEM if actor_id is None else ActorType.ADMIN,
            actor_id=actor_id,
            action=AuditAction.AGENT_CREATED.value,
            entity_type="agent",
            entity_id=agent["id"],
            metadata=agent,
        )
        return agent

    async def update_agent(self, agent_id: str, payload: dict, actor_id: str | None = None) -> dict:
        if "telegram_username" in payload and payload["telegram_username"]:
            payload["telegram_username"] = str(payload["telegram_username"]).lstrip("@")
        agent = await self.repository.update_agent(agent_id, payload)
        await self.audit_service.log(
            actor_type=ActorType.SYSTEM if actor_id is None else ActorType.ADMIN,
            actor_id=actor_id,
            action=AuditAction.AGENT_UPDATED.value,
            entity_type="agent",
            entity_id=agent_id,
            metadata=payload,
        )
        return agent

    async def delete_agent(self, agent_id: str, actor_id: str | None = None) -> dict:
        agent = await self.repository.deactivate_agent(agent_id)
        await self.audit_service.log(
            actor_type=ActorType.SYSTEM if actor_id is None else ActorType.ADMIN,
            actor_id=actor_id,
            action=AuditAction.AGENT_DELETED.value,
            entity_type="agent",
            entity_id=agent_id,
            metadata={"is_active": False},
        )
        return agent

    async def register_private_chat(self, telegram_username: str | None, chat_id: int) -> dict | None:
        agent = await self.find_agent(username=telegram_username, chat_id=None)
        if not agent:
            return None
        if agent.get("telegram_chat_id") == chat_id:
            return agent
        return await self.repository.update_agent(agent["id"], {"telegram_chat_id": chat_id})

    @staticmethod
    def is_privileged(agent: dict | None) -> bool:
        if not agent or not agent.get("is_active"):
            return False
        return agent.get("role") in {AgentRole.MANAGER.value, AgentRole.ADMIN.value}
