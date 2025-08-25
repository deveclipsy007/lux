from typing import Any, Dict, List, Optional

from .client import run as run_query


class InstanceRepo:
    """Asynchronous CRUD interface for WhatsApp instances."""

    async def create(self, data: Dict[str, Any], tx: Any = None) -> Dict[str, Any]:
        payload = {"data": data}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("create_instance", payload)

    async def get(self, instance_id: int, tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": instance_id}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("get_instance", payload)

    async def list(self, tx: Any = None) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        if tx is not None:
            payload["tx"] = tx
        rows = await run_query("list_instances", payload)
        return rows or []

    async def update(self, instance_id: int, data: Dict[str, Any], tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": instance_id, "data": data}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("update_instance", payload)

    async def delete(self, instance_id: int, tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": instance_id}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("delete_instance", payload)
