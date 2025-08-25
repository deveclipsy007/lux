from typing import Any, Dict, List, Optional

from .client import run as run_query


class ConversationRepo:
    """Asynchronous CRUD interface for conversations."""

    async def create(self, data: Dict[str, Any], tx: Any = None) -> Dict[str, Any]:
        payload = {"data": data}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("create_conversation", payload)

    async def get(self, chat_id: str, tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"chatId": chat_id}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("get_conversation", payload)

    async def list(self, instance_id: Optional[int] = None, tx: Any = None) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        if instance_id is not None:
            payload["instanceId"] = instance_id
        if tx is not None:
            payload["tx"] = tx
        rows = await run_query("list_conversations", payload)
        return rows or []

    async def update(self, chat_id: str, data: Dict[str, Any], tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"chatId": chat_id, "data": data}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("update_conversation", payload)

    async def delete(self, chat_id: str, tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"chatId": chat_id}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("delete_conversation", payload)
