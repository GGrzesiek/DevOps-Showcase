import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import create_app


@pytest.fixture
def client():
    application = create_app()
    application.config["TESTING"] = True
    with application.test_client() as c:
        yield c
