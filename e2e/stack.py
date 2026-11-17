"""Start an isolated Supr stack for browser tests.

A fresh, seeded SQLite database in a temporary folder, the FastAPI backend on
port 8101 and the Vite frontend on port 5181 (proxying /api to that backend).
Nothing touches backend/supr.db or the servers on ports 8000/5173.

Run directly to keep a stack up for manual exploration:
    backend/.venv311/Scripts/python.exe e2e/stack.py
"""
import os, subprocess, sys, tempfile, time, urllib.request, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
PYTHON = BACKEND / ".venv311" / "Scripts" / "python.exe"
API_PORT, WEB_PORT = 8101, 5181
API = f"http://127.0.0.1:{API_PORT}"
WEB = f"http://127.0.0.1:{WEB_PORT}"
PASSWORD = "Demo@12345"  # seed demo password, test database only


def _wait(url, seconds=60):
    end = time.time() + seconds
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status < 500: return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"{url} did not start in {seconds}s")


def call(method, path, body=None, token=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read() or b"null")


def token(email):
    return call("POST", "/api/auth/login", {"email": email, "password": PASSWORD})["access_token"]


def prepare_data():
    """Approve three vendors (Greenox stays pending for the approval test) and stock Kathi Junction's menu."""
    admin = token("admin@supr.bmu.edu.in")
    for app in call("GET", "/api/admin/applications", token=admin):
        if app["business_name"] in ("Kathi Junction", "Kolkata's Lazeez", "Domino's"):
            call("POST", f"/api/admin/applications/{app['id']}/decision", {"decision": "approved", "agreement_valid": True, "remarks": "E2E setup"}, admin)
    for vendor in ("kathijunction@supr.demo", "dominos@supr.demo"):
        call("POST", "/api/vendor/products/availability", {"available": True}, token(vendor))


class Stack:
    def __init__(self, web=True):
        self.web = web
        self.tmp = Path(tempfile.mkdtemp(prefix="supr-e2e-"))
        self.env = {**os.environ, "DATABASE_URL": f"sqlite:///{(self.tmp / 'e2e.db').as_posix()}",
                    "UPLOAD_DIR": str(self.tmp / "uploads"), "ALLOWED_ORIGINS": WEB,
                    "SECRET_KEY": "e2e-only-secret-key-that-is-long-enough-123", "SUPR_API_URL": API,
                    "PYTHONIOENCODING": "utf-8"}
        self.procs = []

    def start(self):
        subprocess.run([str(PYTHON), "-m", "app.seed"], cwd=BACKEND, env=self.env, check=True, capture_output=True)
        workers = os.environ.get("SUPR_WORKERS")  # optional: number of uvicorn worker processes
        self.procs.append(subprocess.Popen([str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(API_PORT), *(["--workers", workers] if workers else [])],
                                           cwd=BACKEND, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        npx = "npx.cmd" if os.name == "nt" else "npx"
        if self.web: self.procs.append(subprocess.Popen([npx, "vite", "--host", "127.0.0.1", "--port", str(WEB_PORT), "--strictPort"],
                                           cwd=FRONTEND, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        _wait(API + "/api/health")
        if self.web:
            _wait(WEB); _wait(WEB + "/src/main.tsx", 120); _wait(WEB + "/src/App.tsx", 120)  # let Vite compile once before tests
        prepare_data()
        return self

    def stop(self):
        for p in self.procs:
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
            else:
                p.terminate()
        shutil.rmtree(self.tmp, ignore_errors=True)


if __name__ == "__main__":
    s = Stack().start()
    print(f"Isolated stack up: {WEB} (API {API}). Ctrl+C to stop.", flush=True)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        s.stop()
