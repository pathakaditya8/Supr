import base64, hashlib, hmac, json, secrets, time
from pwdlib import PasswordHash
from .config import ACCESS_TOKEN_MINUTES, SECRET_KEY

password_hash = PasswordHash.recommended()
def hash_password(password: str) -> str: return password_hash.hash(password)
def verify_password(password: str, hashed: str) -> bool: return password_hash.verify(password, hashed)
def issue_token(user_id: int, role: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"sub": user_id, "role": role, "exp": int(time.time()) + ACCESS_TOKEN_MINUTES*60}).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    return payload + "." + base64.urlsafe_b64encode(sig).decode().rstrip("=")
def read_token(token: str):
    try:
        payload, sig = token.split(".")
        expected = base64.urlsafe_b64encode(hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()).decode().rstrip("=")
        if not hmac.compare_digest(sig, expected): return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return data if data["exp"] > time.time() else None
    except Exception: return None
