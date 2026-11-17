import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./supr.db")
# Hosts such as Render hand out "postgres://..." URLs; SQLAlchemy needs the driver named explicitly.
for _prefix in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(_prefix):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(_prefix):]
SECRET_KEY = os.getenv("SECRET_KEY", "local-demo-only-change-this-secret-key")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must contain at least 32 characters")
