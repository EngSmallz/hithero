import argparse

from backend.jobs.runner import run_one_shot_job


def main():
    parser = argparse.ArgumentParser(description="Run one backend job to completion.")
    parser.add_argument(
        "job",
        choices=("daily", "tuesday", "wednesday", "thursday"),
    )
    args = parser.parse_args()

    import app

    job = getattr(app, f"{args.job}_job")
    result = run_one_shot_job(args.job, job)
    if not result.succeeded:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
