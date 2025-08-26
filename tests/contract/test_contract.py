import os
import sys
import schemathesis

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, ROOT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)
from main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


def test_health_contract():
    case = schema.get_case("/api/health", "get")
    response = case.call_asgi()
    case.validate_response(response)
