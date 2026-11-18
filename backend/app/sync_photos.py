r"""Copy dish and section photo rows from the local database into the hosted one (safe to repeat).

The photos are fetched from Unsplash into the local database (python -m app.dish_photos). The live site has its own
database, so after fetching run this once from backend/:

    $env:TARGET_DATABASE_URL = "postgresql://..."        (the Render External Database URL)
    .venv311\Scripts\python -m app.sync_photos

It adds missing photos and updates changed ones. It never deletes anything and touches no other table.
"""
import os
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .copy_data import normalise
from .models import DishPhoto, MenuSectionPhoto


def main():
    target_url = os.environ.get("TARGET_DATABASE_URL", "").strip()
    if not target_url: sys.exit("Set TARGET_DATABASE_URL to the hosted database URL.")
    source = create_engine(normalise(os.environ.get("SOURCE_DATABASE_URL", "sqlite:///./supr.db")))
    target = create_engine(normalise(target_url), pool_pre_ping=True)
    added = updated = 0
    with Session(source) as src, Session(target) as dst:
        for model, key_columns in ((DishPhoto, ("key",)), (MenuSectionPhoto, ("vendor_id", "menu_section", "dietary"))):
            columns = [c.name for c in model.__table__.columns if c.name != "id"]
            for row in src.scalars(select(model)):
                values = {c: getattr(row, c) for c in columns}
                existing = dst.scalar(select(model).filter_by(**{k: values[k] for k in key_columns}))
                if existing is None: dst.add(model(**values)); added += 1
                elif any(getattr(existing, c) != values[c] for c in columns): [setattr(existing, c, values[c]) for c in columns]; updated += 1
        dst.commit()
    print(f"Photos added: {added}, updated: {updated}.")


if __name__ == "__main__":
    main()
