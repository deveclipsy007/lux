import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import aiosqlite
from loguru import logger

from models import Agent, AgentStatus


class AgentRepository:
    """Thin repository layer backed by the `agents` table."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:./data.db")
        if self.database_url.startswith("sqlite:"):
            self.db_path = self.database_url.split("sqlite:", 1)[1]
        else:
            # Fallback for paths without scheme
            self.db_path = self.database_url

    async def init(self) -> None:
        """Initialise database schema if needed."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialization TEXT,
                    instructions TEXT,
                    status TEXT NOT NULL DEFAULT 'draft',
                    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
                )
                """
            )
            await db.commit()

    async def list_agents(self) -> List[Agent]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, name, specialization, instructions, status, created_at, updated_at FROM agents"
            )
            rows = await cursor.fetchall()
        return [self._row_to_agent(row) for row in rows]

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, name, specialization, instructions, status, created_at, updated_at FROM agents WHERE id = ?",
                (agent_id,),
            )
            row = await cursor.fetchone()
        return self._row_to_agent(row) if row else None

    async def create_agent(self, data: Dict[str, Any]) -> Agent:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("BEGIN")
                cursor = await db.execute(
                    "INSERT INTO agents (name, specialization, instructions, status) VALUES (?, ?, ?, ?)",
                    (
                        data["name"],
                        data.get("specialization"),
                        data.get("instructions"),
                        data.get("status", AgentStatus.DRAFT.value),
                    ),
                )
                agent_id = cursor.lastrowid
                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to create agent: {e}")
                raise
        agent = await self.get_agent(agent_id)
        assert agent is not None
        # Adiciona campos não persistidos
        agent.tools = list(data.get("tools", []))
        agent.config = data.get("config", {})
        return agent

    async def update_agent(self, agent_id: str, data: Dict[str, Any]) -> Optional[Agent]:
        fields = []
        values: List[Any] = []
        for column in ("name", "specialization", "instructions", "status"):
            if column in data:
                fields.append(f"{column} = ?")
                values.append(data[column])
        if not fields:
            return await self.get_agent(agent_id)
        values.append(agent_id)
        query = f"UPDATE agents SET {', '.join(fields)}, updated_at = strftime('%s','now') WHERE id = ?"
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("BEGIN")
                cursor = await db.execute(query, values)
                await db.commit()
                if cursor.rowcount == 0:
                    return None
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to update agent {agent_id}: {e}")
                raise
        agent = await self.get_agent(agent_id)
        if agent:
            if "tools" in data and data["tools"] is not None:
                agent.tools = list(data["tools"])
            if "config" in data and data["config"] is not None:
                agent.config.update(data["config"])
        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("BEGIN")
                cursor = await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
                await db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to delete agent {agent_id}: {e}")
                raise

    def _row_to_agent(self, row: aiosqlite.Row) -> Agent:
        status_value = row["status"] or AgentStatus.DRAFT.value
        try:
            status = AgentStatus(status_value)
        except ValueError:
            status = AgentStatus.DRAFT
        return Agent(
            id=str(row["id"]),
            name=row["name"],
            specialization=row["specialization"] or "",
            instructions=row["instructions"] or "",
            tools=[],
            status=status,
            created_at=self._to_datetime(row["created_at"]),
            updated_at=self._to_datetime(row["updated_at"]),
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
