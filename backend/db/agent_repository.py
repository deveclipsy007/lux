import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from ..context import get_correlation_id

from models import Agent, AgentStatus
from .client import run as run_query


class AgentRepository:
    """Repository backed by Drizzle queries executed via Node bridge."""

    async def init(self) -> None:
        """Initialise database schema if needed via Node bridge."""
        try:
            await run_query("init")
        except Exception as exc:
            logger.bind(correlation_id=get_correlation_id()).error(
                f"Failed to initialise database: {exc}"
            )
            raise

    async def list_agents(self) -> List[Agent]:
        rows = await run_query("list")
        return [self._row_to_agent(row) for row in rows or []]

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        row = await run_query("get", {"id": int(agent_id)})
        return self._row_to_agent(row) if row else None

    async def get_agent_by_name(self, name: str) -> Optional[Agent]:
        row = await run_query("get_by_name", {"name": name})
        return self._row_to_agent(row) if row else None

    async def create_agent(self, data: Dict[str, Any]) -> Agent:
        try:
            row = await run_query("create", data)
        except RuntimeError as exc:
            if "UNIQUE" in str(exc):
                existing = await self.get_agent_by_name(data["name"])
                if existing:
                    existing.tools = list(data.get("tools", []))
                    existing.config = data.get("config", {})
                    return existing
            raise
        agent = self._row_to_agent(row)
        agent.tools = list(data.get("tools", []))
        agent.config = data.get("config", {})
        return agent

    async def update_agent(self, agent_id: str, data: Dict[str, Any]) -> Optional[Agent]:
        row = await run_query("update", {"id": int(agent_id), "data": data})
        if not row:
            return None
        agent = self._row_to_agent(row)
        if "tools" in data and data["tools"] is not None:
            agent.tools = list(data["tools"])
        if "config" in data and data["config"] is not None:
            agent.config.update(data["config"])
        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        result = await run_query("delete", {"id": int(agent_id)})
        return bool(result)

    def _row_to_agent(self, row: Dict[str, Any]) -> Agent:
        status_value = row.get("status") or AgentStatus.DRAFT.value
        try:
            status = AgentStatus(status_value)
        except ValueError:
            status = AgentStatus.DRAFT
        return Agent(
            id=str(row["id"]),
            name=row["name"],
            specialization=row.get("specialization") or "",
            instructions=row.get("instructions") or "",
            tools=[],
            status=status,
            created_at=self._to_datetime(row.get("createdAt")),
            updated_at=self._to_datetime(row.get("updatedAt")),
            config={},
        )

    @staticmethod
    def _to_datetime(value: Any) -> datetime:
        if value is None:
            return datetime.now()
        if isinstance(value, (int, float)):
            if value > 1e12:
                value /= 1000.0
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.now()
        return datetime.now()
