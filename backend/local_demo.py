"""SQLite-only bootstrap and checked-in demo fixtures for local workflows."""

import csv
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.engine import make_url

from backend.db.base import Base
from backend.db.models import School, TeacherList
from backend.db.session import create_database_resources


DEMO_SCHOOL_COUNT = 100
DEMO_TEACHER_COUNT = 50
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "fixtures"
SCHOOLS_FIXTURE = "schools.csv"
TEACHERS_FIXTURE = "fake-public-teachers.csv"
SCHOOL_HEADERS = ("state", "county", "district", "school_name")
TEACHER_HEADERS = ("name", "state", "county", "district", "school", "about_me", "url_id")


@dataclass(frozen=True)
class LocalDemoSeedResult:
    database_url: str
    schools_added: int
    teachers_added: int


def _require_sqlite(database_url: str) -> None:
    try:
        drivername = make_url(database_url).drivername
    except Exception as exc:
        raise ValueError("Local demo bootstrap requires a valid SQLite URL") from exc
    if not drivername.startswith("sqlite"):
        raise ValueError("Local demo bootstrap only accepts SQLite database URLs")


def _read_fixture(
    fixture_dir: Path,
    filename: str,
    expected_headers: tuple[str, ...],
) -> list[dict[str, str]]:
    path = fixture_dir / filename
    try:
        with path.open(newline="", encoding="utf-8") as fixture:
            reader = csv.DictReader(fixture)
            headers = tuple(reader.fieldnames or ())
            if headers != expected_headers:
                raise ValueError(
                    f"{path} must have headers {','.join(expected_headers)}"
                )
            rows = list(reader)
    except FileNotFoundError as exc:
        raise ValueError(f"Missing local demo fixture: {path}") from exc

    if any(not all((value or "").strip() for value in row.values()) for row in rows):
        raise ValueError(f"{path} contains an empty fixture value")
    return rows


def _read_demo_fixtures(fixture_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    schools = _read_fixture(fixture_dir, SCHOOLS_FIXTURE, SCHOOL_HEADERS)
    teachers = _read_fixture(fixture_dir, TEACHERS_FIXTURE, TEACHER_HEADERS)
    if len(schools) != DEMO_SCHOOL_COUNT:
        raise ValueError(f"{SCHOOLS_FIXTURE} must contain {DEMO_SCHOOL_COUNT} rows")
    if len(teachers) != DEMO_TEACHER_COUNT:
        raise ValueError(f"{TEACHERS_FIXTURE} must contain {DEMO_TEACHER_COUNT} rows")
    if len({row["school_name"] for row in schools}) != len(schools):
        raise ValueError(f"{SCHOOLS_FIXTURE} contains duplicate school names")
    if len({row["url_id"] for row in teachers}) != len(teachers):
        raise ValueError(f"{TEACHERS_FIXTURE} contains duplicate url_id values")
    school_keys = {
        (row["state"], row["county"], row["district"], row["school_name"])
        for row in schools
    }
    for teacher in teachers:
        teacher_school = (
            teacher["state"],
            teacher["county"],
            teacher["district"],
            teacher["school"],
        )
        if teacher_school not in school_keys:
            raise ValueError(
                f"{TEACHERS_FIXTURE} references a school missing from {SCHOOLS_FIXTURE}: "
                f"{teacher['school']}"
            )
    return schools, teachers


def bootstrap_local_database(
    database_url: str,
    *,
    fixture_dir: Path = FIXTURE_DIR,
) -> LocalDemoSeedResult:
    """Create local SQLite tables and insert missing deterministic demo rows."""
    _require_sqlite(database_url)
    demo_schools, demo_teachers = _read_demo_fixtures(fixture_dir)
    resources = create_database_resources("test", database_url=database_url)
    try:
        Base.metadata.create_all(bind=resources.engine)
        db = resources.session_factory()
        schools_added = 0
        teachers_added = 0
        try:
            school_rows = {}
            for school_data in demo_schools:
                school = db.execute(
                    select(School).where(
                        School.state == school_data["state"],
                        School.county == school_data["county"],
                        School.district == school_data["district"],
                        School.school_name == school_data["school_name"],
                    )
                ).scalar_one_or_none()
                if school is None:
                    school = School(**school_data)
                    db.add(school)
                    schools_added += 1
                school_rows[school_data["school_name"]] = school_data

            db.flush()
            for teacher_data in demo_teachers:
                school = school_rows[teacher_data["school"]]
                existing = db.execute(
                    select(TeacherList).where(TeacherList.url_id == teacher_data["url_id"])
                ).scalar_one_or_none()
                if existing is None:
                    db.add(TeacherList(**teacher_data))
                    teachers_added += 1
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return LocalDemoSeedResult(
            database_url=database_url,
            schools_added=schools_added,
            teachers_added=teachers_added,
        )
    finally:
        resources.engine.dispose()


__all__ = [
    "DEMO_SCHOOL_COUNT",
    "DEMO_TEACHER_COUNT",
    "LocalDemoSeedResult",
    "bootstrap_local_database",
]
