"""Copy the local SQLite data into a new (empty) hosted database such as Render PostgreSQL.

Run from backend/, once, after the hosted database exists:

    set TARGET_DATABASE_URL=postgresql://user:password@host/dbname      (PowerShell: $env:TARGET_DATABASE_URL="...")
    set ADMIN_PASSWORD=choose-a-strong-password-of-12-or-more-characters
    python -m app.copy_data

What it does
- creates the tables in the target and copies the catalogue (menus, photos, vendors, listed shops, categories),
  but not test orders, carts or notifications from development;
- refuses to run if the target already contains data;
- replaces the demo passwords: the admin gets ADMIN_PASSWORD, the demo student account is disabled, and each
  vendor account gets a new random password that is printed once at the end (store it, then give it to the vendor);
- resets PostgreSQL id counters so new rows get fresh ids.

The source defaults to the local database (sqlite:///./supr.db); override with SOURCE_DATABASE_URL.
"""
import os
import secrets
import sys

from sqlalchemy import Integer, create_engine, func, inspect, select, text
from sqlalchemy.orm import Session

from . import models  # noqa: F401  (registers all tables)
from .database import Base
from .models import User
from .security import hash_password

# Test orders, carts and notifications made while developing are not copied to the live database.
SKIP = {"orders", "order_items", "carts", "cart_items", "notifications"}


def normalise(url):
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def main():
    target_url = os.environ.get("TARGET_DATABASE_URL", "").strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if not target_url: sys.exit("Set TARGET_DATABASE_URL to the hosted database URL.")
    if len(admin_password) < 12: sys.exit("Set ADMIN_PASSWORD to a strong password of at least 12 characters.")
    source = create_engine(normalise(os.environ.get("SOURCE_DATABASE_URL", "sqlite:///./supr.db")))
    target = create_engine(normalise(target_url), pool_pre_ping=True)
    if source.url == target.url: sys.exit("Source and target are the same database.")

    Base.metadata.create_all(target)
    with target.connect() as c:
        if c.execute(select(func.count()).select_from(User)).scalar():
            sys.exit("The target database already has users; refusing to copy over existing data.")

    available = set(inspect(source).get_table_names())
    copied = {}
    with source.connect() as src, target.begin() as dst:
        for table in Base.metadata.sorted_tables:
            if table.name not in available or table.name in SKIP: continue
            rows = [dict(r._mapping) for r in src.execute(select(table))]
            if rows: dst.execute(table.insert(), rows)
            copied[table.name] = len(rows)
        if target.dialect.name == "postgresql":                       # explicit ids were copied; move the counters past them
            for table in Base.metadata.sorted_tables:
                pk = [c for c in table.primary_key.columns if isinstance(c.type, Integer)]
                if len(pk) == 1 and copied.get(table.name):
                    dst.execute(text(f"SELECT setval(pg_get_serial_sequence('{table.name}', '{pk[0].name}'), "
                                     f"(SELECT MAX({pk[0].name}) FROM {table.name}))"))

    credentials = []
    with Session(target) as db:
        for user in db.scalars(select(User).order_by(User.id)):
            if user.role == "admin":
                user.password_hash = hash_password(admin_password)
            elif user.role == "student":
                user.enabled = False                                    # demo student; admin creates real accounts
                user.password_hash = hash_password(secrets.token_urlsafe(32))
            elif user.enabled:                                          # vendor accounts that can sign in
                password = secrets.token_urlsafe(12)
                user.password_hash = hash_password(password)
                credentials.append((user.email, password))
        db.commit()

    print("Copied rows per table:")
    for name, count in copied.items(): print(f"  {name:<28} {count}")
    print("\nAdmin sign-in: admin@supr.bmu.edu.in with the ADMIN_PASSWORD you set.")
    print("The demo student account is disabled; create real student accounts from the admin screen.")
    print("\nVendor accounts (shown once; give each vendor their own password and ask them to keep it private):")
    for email, password in credentials: print(f"  {email:<34} {password}")


if __name__ == "__main__":
    main()
