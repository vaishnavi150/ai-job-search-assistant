"""Creates all tables. Run once before starting the app for the first time.

    python scripts/init_db.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, engine
import app.models  # noqa: F401 - registers models on Base


def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


if __name__ == "__main__":
    main()
