import asyncio
import json
import os
import logging
from typing import Any, Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE_SCRIPT = os.path.normpath(os.path.join(BASE_DIR, "..", "database", "bridge.ts"))

logger = logging.getLogger(__name__)

async def run(action: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    """Execute Drizzle queries through the Node bridge."""
    payload_json = json.dumps(payload or {})
    env = os.environ.copy()
    env.setdefault("DB_PROVIDER", "sqlite")
    env.setdefault("DATABASE_URL", "sqlite:./data.db")
    proc = await asyncio.create_subprocess_exec(
        "npx", "tsx", BRIDGE_SCRIPT, action, payload_json,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err = stderr.decode().strip()
        logger.error("Node bridge failed: %s", err)
        raise RuntimeError(f"Node bridge failed: {err}")
    out = stdout.decode().strip()
    return json.loads(out) if out else None
