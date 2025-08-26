import os
import sys

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT_DIR)

import backend.models as backend_models
sys.modules["models"] = backend_models

from backend.db.agent_repository import AgentRepository


@pytest.mark.asyncio
async def test_create_agent_success():
    repo = AgentRepository()
    data = {
        "name": "agent1",
        "specialization": "spec",
        "instructions": "i" * 80,
        "tools": ["t1"],
        "config": {"a": 1},
    }
    agent = await repo.create_agent(data)
    assert agent.id == "1"
    assert agent.name == "agent1"
    assert agent.tools == ["t1"]
    assert agent.config == {"a": 1}


@pytest.mark.asyncio
async def test_create_agent_duplicate_returns_existing():
    repo = AgentRepository()
    data = {
        "name": "agent1",
        "specialization": "spec",
        "instructions": "i" * 80,
        "tools": ["t1"],
        "config": {"a": 1},
    }
    first = await repo.create_agent(data)
    data["tools"] = ["t2"]
    data["config"] = {"b": 2}
    second = await repo.create_agent(data)
    assert second.id == first.id
    assert second.tools == ["t2"]
    assert second.config == {"b": 2}


@pytest.mark.asyncio
async def test_create_agent_validation_error():
    repo = AgentRepository()
    data = {
        "specialization": "spec",
        "instructions": "i" * 80,
        "tools": ["t1"],
    }
    with pytest.raises(RuntimeError):
        await repo.create_agent(data)
