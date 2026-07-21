"""Add the alternate school needed for local school-change manual testing.

This is intentionally a small SQLite data seed. It does not create tables,
run migrations, or target production databases.
"""

import argparse
import sqlite3
from pathlib import Path


SEED_SCHOOL = {
    "state": "Washington",
    "county": "King",
    "district": "Seattle Public Schools",
    "school_name": "Roosevelt High School",
}


def seed_school(database_path: Path) -> bool:
    if not database_path.is_file():
        raise FileNotFoundError(f"Local SQLite database does not exist: {database_path}")

    with sqlite3.connect(database_path) as connection:
        existing = connection.execute(
            """
            SELECT 1
            FROM schools
            WHERE state = :state
              AND county = :county
              AND district = :district
              AND school_name = :school_name
            LIMIT 1
            """,
            SEED_SCHOOL,
        ).fetchone()
        if existing:
            return False

        connection.execute(
            """
            INSERT INTO schools (state, county, district, school_name)
            VALUES (:state, :county, :district, :school_name)
            """,
            SEED_SCHOOL,
        )
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=Path(".local/hithero-dev.sqlite"),
        help="Disposable local SQLite database path (default: .local/hithero-dev.sqlite)",
    )
    args = parser.parse_args()
    added = seed_school(args.database)
    school = SEED_SCHOOL["school_name"]
    print(f"{school}: {'added' if added else 'already present'} in {args.database}")


if __name__ == "__main__":
    main()
