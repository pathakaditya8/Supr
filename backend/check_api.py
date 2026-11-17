import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
print('building test client', flush=True)
with TestClient(app) as client:
    print('client ready', flush=True)
    print(client.get('/api/health', timeout=5).status_code, flush=True)
print('complete', flush=True)
