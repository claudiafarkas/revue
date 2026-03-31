"""Entry point for running SQL migrations manually."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.services.database import connection_string, initialize_database


def main() -> None:
    print("Using database connection:", connection_string(mask_password=True))
    initialize_database()
    print("Migrations applied successfully.")


if __name__ == "__main__":
    main()
