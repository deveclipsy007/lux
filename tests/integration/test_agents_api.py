import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT_DIR)

import backend.models as backend_models
sys.modules["models"] = backend_models

import backend.db as backend_db
import backend.db.agent_repository as backend_ar
sys.modules["db"] = backend_db
sys.modules["db.agent_repository"] = backend_ar

import types

schemas_module = types.ModuleType("schemas")
sys.modules["schemas"] = schemas_module

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class AgentCreate(BaseModel):
    agent_name: str
    instructions: str
    specialization: str
    tools: List[str]
    integrations: Optional[Dict[str, Any]] = None


class AgentInfo(BaseModel):
    id: str
    name: str
    specialization: str
    instructions: str
    tools: List[str]
    status: str = "draft"
    config: Dict[str, Any] = {}


class AgentUpdate(BaseModel):
    pass


class AgentGeneratedFiles(BaseModel):
    pass


class InstanceState(BaseModel):
    pass


class SendMessage(BaseModel):
    pass


class HealthResponse(BaseModel):
    pass


class LogEntry(BaseModel):
    pass


class MaterializeRequest(BaseModel):
    pass


class StatusResponse(BaseModel):
    pass


class ServiceChecks(BaseModel):
    pass


schemas_module.AgentCreate = AgentCreate
schemas_module.AgentGeneratedFiles = AgentGeneratedFiles
schemas_module.InstanceState = InstanceState
schemas_module.SendMessage = SendMessage
schemas_module.HealthResponse = HealthResponse
schemas_module.LogEntry = LogEntry
schemas_module.MaterializeRequest = MaterializeRequest
schemas_module.AgentInfo = AgentInfo
schemas_module.AgentUpdate = AgentUpdate
schemas_module.StatusResponse = StatusResponse
schemas_module.ServiceChecks = ServiceChecks

services_module = types.ModuleType("services")

class DummyGenerator:
    def __init__(self, *args, **kwargs):
        pass

class DummyEvolution:
    def __init__(self, *args, **kwargs):
        pass

    async def test_connection(self):
        return None

class DummyAgno:
    def __init__(self, *args, **kwargs):
        pass

generator_mod = types.ModuleType("generator")
generator_mod.CodeGeneratorService = DummyGenerator

evolution_mod = types.ModuleType("evolution")
evolution_mod.EvolutionService = DummyEvolution

agno_mod = types.ModuleType("agno")
agno_mod.AgnoService = DummyAgno

services_module.generator = generator_mod
services_module.evolution = evolution_mod
services_module.agno = agno_mod

sys.modules["services"] = services_module
sys.modules["services.generator"] = generator_mod
sys.modules["services.evolution"] = evolution_mod
sys.modules["services.agno"] = agno_mod

import backend.context as backend_context
sys.modules["context"] = backend_context

from backend.main import app, get_current_user


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: {"user": "test"}
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_agent_endpoint_idempotent(client):
    payload = {
        "agent_name": "agent1",
        "instructions": "i" * 80,
        "specialization": "Atendimento",
        "tools": ["calendar"],
    }
    resp1 = client.post("/api/agents", json=payload)
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["name"] == payload["agent_name"]
    assert data1["tools"] == ["calendar"]

    resp2 = client.post("/api/agents", json=payload)
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["id"] == data1["id"]
