from __future__ import annotations
import argparse
import sys
from getpass import getpass
from app.db.seed import admin_exists, create_admin_user, get_user_by_email, seed_roles
from app.db.session import SessionLocal

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the first admin user for the platform."
    )
    parser.add_argument("--email", help="Admin email")
    parser.add_argument("--full-name", help="Admin full name")
    parser.add_argument("--position", help="Admin position", default=None)
    parser.add_argument("--department", help="Admin department", default=None)
    parser.add_argument(
        "--allow-second-admin",
        action="store_true",
        help="Allow creating admin even if another admin already exists.",
    )
    return parser.parse_args()

def prompt_if_empty(value: str | None, prompt_text: str) -> str:
    if value and value.strip():
        return value.strip()
    return input(prompt_text).strip()

def main() -> int:
    args = parse_args()
    db = SessionLocal()

    try:
        seed_roles(db)

        if admin_exists(db) and not args.allow_second_admin:
            print(
                "An admin user already exists. "
                "Use --allow-second-admin only if you intentionally want another one."
            )
            return 1

        email = prompt_if_empty(args.email, "Admin email: ").lower()
        full_name = prompt_if_empty(args.full_name, "Full name: ")
        position = args.position if args.position is not None else input("Position (optional): ").strip() or None
        department = args.department if args.department is not None else input("Department (optional): ").strip() or None
        password = getpass("Admin password: ")
        password_repeat = getpass("Repeat password: ")

        if password != password_repeat:
            print("Passwords do not match.")
            return 1

        existing_user = get_user_by_email(db, email)
        if existing_user is not None:
            print(f"User with email '{email}' already exists.")
            return 1

        user = create_admin_user(
            db,
            email=email,
            password=password,
            full_name=full_name,
            position=position,
            department=department,
        )

        print(f"Admin user created successfully: {user.email}")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    raise SystemExit(main())