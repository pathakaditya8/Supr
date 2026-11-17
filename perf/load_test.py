"""Performance and concurrency test for the Supr API (CSE3005 performance testing).

Starts an isolated backend (port 8101, freshly seeded temporary SQLite database),
then measures response times while 1, 10, 25 and 50 simulated users act at once,
and finally checks that simultaneous checkouts never sell more stock than exists.

Run from the project root:
    backend/.venv311/Scripts/python.exe perf/load_test.py
Results are printed and saved to perf/results-<date>.json.
"""
import json, os, platform, statistics, sys, threading, time, datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "e2e"))
from stack import Stack, API, PASSWORD, call, token  # noqa: E402

LEVELS = [1, 10, 25, 50]          # concurrent simulated users
DURATION = 15                     # seconds per scenario and level
STUDENT_PASSWORD = "Perf@123456"  # throwaway accounts in the temporary database only
# Assumed targets for a single-campus marketplace (see docs/TEST_PLAN.md).
TARGETS = {"browse": 500, "login": 1500, "order": 1000}  # p95 in milliseconds at 25 users


def percentile(values, pct):
    if not values: return None
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct / 100
    lo, hi = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def make_students(n):
    admin = token("admin@supr.bmu.edu.in")
    stamp = time.time_ns()
    emails = []
    for i in range(n):
        email = f"perf{stamp}-{i}@supr.test"
        call("POST", "/api/admin/students", {"name": f"Perf Student {i}", "email": email, "phone": "9000000000", "password": STUDENT_PASSWORD}, admin)
        emails.append(email)
    return emails


def login_token(client, email):
    r = client.post("/api/auth/login", json={"email": email, "password": STUDENT_PASSWORD})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def catalogue_ids():
    with httpx.Client(base_url=API) as c:
        kathi = next(v for v in c.get("/api/vendors").json() if v["business_name"] == "Kathi Junction")
        items = c.get("/api/products", params={"vendor_id": kathi["id"], "available_only": True, "limit": 100}).json()["items"]
        simple = [p["id"] for p in items if not p["variants"]]
        return kathi["id"], simple


def run_level(name, users, action_factory):
    """Each simulated user repeats its action for DURATION seconds; returns latency stats."""
    latencies, errors, lock = [], [], threading.Lock()
    deadline = time.perf_counter() + DURATION
    def worker(idx):
        with httpx.Client(base_url=API, timeout=30) as client:
            action = action_factory(client, idx)
            while time.perf_counter() < deadline:
                start = time.perf_counter()
                try:
                    ok, detail = action()
                except Exception as e:  # network errors count as failures
                    ok, detail = False, type(e).__name__
                ms = (time.perf_counter() - start) * 1000
                with lock:
                    latencies.append(ms)
                    if not ok: errors.append(detail)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=users) as pool:
        list(pool.map(worker, range(users)))
    elapsed = time.perf_counter() - t0
    result = {"scenario": name, "users": users, "requests": len(latencies), "throughput_rps": round(len(latencies) / elapsed, 1),
              "p50_ms": round(percentile(latencies, 50), 1), "p95_ms": round(percentile(latencies, 95), 1),
              "p99_ms": round(percentile(latencies, 99), 1), "max_ms": round(max(latencies), 1),
              "errors": len(errors), "error_rate_pct": round(100 * len(errors) / max(len(latencies), 1), 2),
              "error_samples": sorted(set(errors))[:5]}
    print(f"  {name:<7} users={users:<3} req={result['requests']:<6} rps={result['throughput_rps']:<7} "
          f"p50={result['p50_ms']:<7} p95={result['p95_ms']:<7} p99={result['p99_ms']:<7} errors={result['errors']}", flush=True)
    return result


def browse_factory(vendor_id, product_ids):
    paths = [("/api/products", {}), ("/api/products", {"q": "paneer"}), ("/api/products", {"category_id": 6, "sort": "price_asc"}),
             ("/api/vendors", {}), ("/api/products", {"vendor_id": vendor_id, "limit": 48})]
    def factory(client, idx):
        i = [idx]
        def action():
            i[0] += 1
            if i[0] % 6 == 0:
                r = client.get(f"/api/products/{product_ids[i[0] % len(product_ids)]}")
            else:
                path, params = paths[i[0] % len(paths)]
                r = client.get(path, params=params)
            return r.status_code == 200, r.status_code
        return action
    return factory


def login_factory(emails):
    def factory(client, idx):
        email = emails[idx % len(emails)]
        def action():
            r = client.post("/api/auth/login", json={"email": email, "password": STUDENT_PASSWORD})
            return r.status_code == 200, r.status_code
        return action
    return factory


def order_factory(emails, product_ids):
    """One full order per iteration: clear cart, add an item, place the order."""
    def factory(client, idx):
        headers = login_token(client, emails[idx])
        n = [idx]
        def action():
            n[0] += 1
            client.delete("/api/cart", headers=headers)
            a = client.post("/api/cart/items", headers=headers, json={"product_id": product_ids[n[0] % len(product_ids)], "quantity": 1})
            if a.status_code != 201: return False, f"add {a.status_code}"
            o = client.post("/api/orders", headers=headers, json={"delivery_location": ""})
            return o.status_code == 201, f"order {o.status_code}"
        return action
    return factory


def oversell_check(emails, stock=5):
    """All students hold the same item in their carts, then check out at the same instant."""
    _, ids = catalogue_ids()
    product_id = ids[0]
    vendor = token("kathijunction@supr.demo")
    call("PATCH", f"/api/vendor/products/{product_id}", {"stock": stock, "available": True}, vendor)
    clients = [httpx.Client(base_url=API, timeout=30) for _ in emails]
    heads = [login_token(c, e) for c, e in zip(clients, emails)]
    for c, h in zip(clients, heads):
        c.delete("/api/cart", headers=h)
        assert c.post("/api/cart/items", headers=h, json={"product_id": product_id, "quantity": 1}).status_code == 201
    gate = threading.Barrier(len(emails))
    def checkout(i):
        gate.wait()
        return clients[i].post("/api/orders", headers=heads[i], json={"delivery_location": ""}).status_code
    with ThreadPoolExecutor(max_workers=len(emails)) as pool:
        codes = list(pool.map(checkout, range(len(emails))))
    for c in clients: c.close()
    with httpx.Client(base_url=API) as c:
        admin = {"Authorization": f"Bearer {token('admin@supr.bmu.edu.in')}"}
        final = next(p for p in c.get("/api/admin/listings", headers=admin).json() if p["id"] == product_id)["stock"]
    result = {"buyers": len(emails), "stock_before": stock, "orders_created": codes.count(201),
              "refused_409": codes.count(409), "other_status": sorted(set(c for c in codes if c not in (201, 409))),
              "stock_after": final, "oversold": codes.count(201) > stock or final < 0}
    print(f"  oversell check: {result}", flush=True)
    return result


def main():
    print("Starting isolated backend…", flush=True)
    stack = Stack(web=False).start()
    try:
        vendor_id, product_ids = catalogue_ids()
        # Give every item plenty of stock so the load scenarios never run out.
        kathi = token("kathijunction@supr.demo")
        for pid in product_ids: call("PATCH", f"/api/vendor/products/{pid}", {"stock": 100000, "available": True}, kathi)
        emails = make_students(max(LEVELS))
        race_emails = make_students(30)
        results = {"date": datetime.date.today().isoformat(), "environment": {
            "os": platform.platform(), "python": platform.python_version(), "cpu_count": os.cpu_count(),
            "server": f"uvicorn, {os.environ.get('SUPR_WORKERS', '1')} worker(s), SQLite (temporary file)", "client": "same machine, httpx thread per user",
            "duration_s_per_level": DURATION}, "targets_p95_ms_at_25_users": TARGETS, "load": [], "oversell": None}
        for name, factory in (("browse", browse_factory(vendor_id, product_ids)), ("login", login_factory(emails)), ("order", order_factory(emails, product_ids))):
            print(f"\nScenario: {name}", flush=True)
            for users in LEVELS:
                results["load"].append(run_level(name, users, factory))
        print("\nConcurrency: simultaneous checkout of the last items", flush=True)
        results["oversell"] = oversell_check(race_emails)
        suffix = f"-{os.environ['SUPR_WORKERS']}workers" if os.environ.get("SUPR_WORKERS") else ""
        out = ROOT / "perf" / f"results-{results['date']}{suffix}.json"
        out.write_text(json.dumps(results, indent=2))
        print(f"\nSaved {out}")
    finally:
        stack.stop()


if __name__ == "__main__":
    main()
