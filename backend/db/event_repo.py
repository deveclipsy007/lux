from typing import Any, Dict, List, Optional

from .client import run as run_query


class EventRepo:
    """Asynchronous CRUD interface for system events."""

    async def init(self) -> None:
        """Initialise event tables via Node bridge."""
        await run_query("init_events")

    async def create(self, data: Dict[str, Any], tx: Any = None) -> Dict[str, Any]:
        payload = {"data": data}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("log_event", payload)

    async def get(self, event_id: int, tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": event_id}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("get_event", payload)

    async def list(self, event_type: Optional[str] = None, tx: Any = None) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {}
        if event_type is not None:
            payload["type"] = event_type
            action = "list_events_by_type"
        else:
            action = "list_events"
        if tx is not None:
            payload["tx"] = tx
        rows = await run_query(action, payload)
        return rows or []

    # Aliases for backwards compatibility
    async def log_event(self, data: Dict[str, Any], tx: Any = None) -> Dict[str, Any]:
        return await self.create(data, tx)

    async def list_events(self, event_type: Optional[str] = None, tx: Any = None) -> List[Dict[str, Any]]:
        return await self.list(event_type, tx)

    async def update(self, event_id: int, data: Dict[str, Any], tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": event_id, "data": data}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("update_event", payload)

    async def delete(self, event_id: int, tx: Any = None) -> Optional[Dict[str, Any]]:
        payload = {"id": event_id}
        if tx is not None:
            payload["tx"] = tx
        return await run_query("delete_event", payload)
