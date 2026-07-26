#!/usr/bin/env python3
"""Create and seed a disposable local SQLite database."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.local_demo import bootstrap_local_database


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    args = parser.parse_args()

    result = bootstrap_local_database(args.database_url)
    print(
        f"Bootstrapped {result.database_url}: "
        f"{result.schools_added} schools added, "
        f"{result.teachers_added} teachers added"
    )


if __name__ == "__main__":
    main()
