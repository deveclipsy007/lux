import pytest
import subprocess


@pytest.fixture(autouse=True)
def mock_database(monkeypatch):
    agents = {}
    next_id = 1

    async def run_query(action, payload=None):
        nonlocal next_id
        payload = payload or {}
        if action in ("init", "init_events"):
            return None
        if action == "list":
            return list(agents.values())
        if action == "get":
            return agents.get(int(payload["id"]))
        if action == "get_by_name":
            name = payload.get("name")
            for row in agents.values():
                if row["name"] == name:
                    return row
            return None
        if action == "create":
            name = payload.get("name")
            if not name:
                raise RuntimeError("validation error")
            for row in agents.values():
                if row["name"] == name:
                    raise RuntimeError("UNIQUE constraint failed")
            row = {
                "id": next_id,
                "name": name,
                "specialization": payload.get("specialization", ""),
                "instructions": payload.get("instructions", ""),
                "status": "draft",
                "createdAt": 0,
                "updatedAt": 0,
            }
            agents[next_id] = row
            next_id += 1
            return row
        if action == "log_event":
            return {"ok": True}
        return None

    monkeypatch.setattr("backend.db.agent_repository.run_query", run_query)
    monkeypatch.setattr("backend.db.event_repo.run_query", run_query)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    try:
        from backend.services.evolution import EvolutionService

        async def fake_test_connection(self):
            return None

        monkeypatch.setattr(
            EvolutionService,
            "test_connection",
            fake_test_connection,
        )
    except ModuleNotFoundError:
        pass

    yield
    agents.clear()
    next_id = 1
