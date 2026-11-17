import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"]="sqlite:///./test_supr.db"
import tempfile, atexit, shutil
os.environ["UPLOAD_DIR"]=tempfile.mkdtemp(prefix="supr-test-uploads-")
atexit.register(shutil.rmtree, os.environ["UPLOAD_DIR"], ignore_errors=True)
os.environ["SECRET_KEY"]="test-secret-key-with-more-than-thirty-two-characters"
import pytest
from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app
from app.seed import *  # test fixture database gets deterministic demo records

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c: yield c

def token(client,email,password="Demo@12345"):
    return client.post("/api/auth/login",json={"email":email,"password":password}).json()["access_token"]

@pytest.fixture
def auth_headers(client):
    return {"student":{"Authorization":"Bearer "+token(client,"student@supr.bmu.edu.in")},"vendor":{"Authorization":"Bearer "+token(client,"kathijunction@supr.demo")},"admin":{"Authorization":"Bearer "+token(client,"admin@supr.bmu.edu.in")}}
