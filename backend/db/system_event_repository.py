import json
from typing import Any, Dict, List, Optional

from loguru import logger

from models import SystemEvent, EventType
from .client import run as run_query


class SystemEventRepository:
    """Repository backed by Drizzle for system events."""

    async def init(self) -> None:
        try:
            await run_query("init_events")
        except Exception as exc:
            logger.error(f"Failed to initialise system events: {exc}")
            raise

    async def log_event(self, event: SystemEvent) -> None:
        payload: Dict[str, Any] = {
            "eventType": event.event_type.value,
            "source": event.source,
            "agentId": int(event.agent_id) if event.agent_id else None,
            "instanceId": int(event.instance_id) if event.instance_id else None,
            "data": json.dumps(event.data, ensure_ascii=False),
        }
        await run_query("log_event", payload)

    async def list_events(
        self, event_type: Optional[EventType] = None
    ) -> List[Dict[str, Any]]:
        action = "list_events_by_type" if event_type else "list_events"
        payload = {"type": event_type.value} if event_type else {}
        rows = await run_query(action, payload)
        return rows or []
