"""Creates all tables and applies column migrations. The app also does this
on startup, so running it by hand is optional.

    python scripts/init_db.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.migrations import run_migrations


def main():
    run_migrations()
    print("Database is up to date.")


if __name__ == "__main__":
    main()
