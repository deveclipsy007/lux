import os
import sys
import schemathesis

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, ROOT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)
from main import app

schema_dict = app.openapi()
schema_dict["openapi"] = "3.0.3"
schema = schemathesis.from_dict(schema_dict, app=app, validate_schema=False)


def test_health_contract():
    case = schema["/api/health"]["get"].make_case()
    response = case.call_asgi()
    case.validate_response(response)
