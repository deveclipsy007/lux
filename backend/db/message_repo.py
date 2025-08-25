from typing import Any, Dict, List, Optional

from .client import run as run_query


class MessageRepo:
    """Asynchronous CRUD interface for messages."""

    async def create(self, data: Dict[str, Any], tx: Any = None) -> Dict[str, Any]:
        payload = {"data": data}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("create_message", payload)

    async def get(self, message_id: int, tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": message_id}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("get_message", payload)

    async def list_by_instance(self, instance_id: int, tx: Any = None) -> List[Dict[str, Any]]:
        payload = {"instanceId": instance_id}
        if tx is not None:
            payload["tx"] = tx
        rows = await run_query("list_messages_by_instance", payload)
        return rows or []

    async def update(self, message_id: int, data: Dict[str, Any], tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": message_id, "data": data}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("update_message", payload)

    async def delete(self, message_id: int, tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": message_id}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("delete_message", payload)
