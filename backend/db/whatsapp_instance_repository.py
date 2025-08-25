"""Repository for persisting WhatsApp instances via Node bridge."""

from typing import Any, Dict, List, Optional

from .client import run as run_query


class WhatsAppInstanceRepository:
    """Simple wrapper around Drizzle queries for whatsapp_instances."""

    async def create_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new whatsapp instance record."""
        return await run_query("create_instance", data)

    async def update_instance(self, instance_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields on an instance and return the updated row."""
        payload = {"id": instance_id, "data": data}
        return await run_query("update_instance", payload)

    async def get_instance(self, instance_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single instance by id."""
        return await run_query("get_instance", {"id": instance_id})

    async def list_instances(self) -> List[Dict[str, Any]]:
        """List all stored instances."""
        rows = await run_query("list_instances")
        return rows or []

