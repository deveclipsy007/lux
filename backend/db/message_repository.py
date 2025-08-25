"""Repository for persisting WhatsApp messages via Node bridge."""

from typing import Any, Dict, List

from .client import run as run_query


class MessageRepository:
    """Wrapper around Drizzle queries for messages."""

    async def log_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new message record."""
        return await run_query("create_message", data)

    async def list_by_instance(self, instance_id: int) -> List[Dict[str, Any]]:
        """Return all messages for a given instance."""
        rows = await run_query("list_messages_by_instance", {"instanceId": instance_id})
        return rows or []

