from __future__ import annotations
from app.core.config import get_settings
from app.db.seed import admin_exists, create_admin_user, seed_roles
from app.db.session import SessionLocal

def init_db() -> None:
    settings = get_settings()
    db = SessionLocal()

    try:
        seed_roles(db)

        admin_enabled = bool(getattr(settings, "admin_bootstrap_enabled", False))
        admin_email = getattr(settings, "admin_bootstrap_email", None)
        admin_password = getattr(settings, "admin_bootstrap_password", None)
        admin_full_name = getattr(settings, "admin_bootstrap_full_name", None)
        admin_position = getattr(settings, "admin_bootstrap_position", None)
        admin_department = getattr(settings, "admin_bootstrap_department", None)

        if not admin_enabled:
            return

        if admin_exists(db):
            return

        if not admin_email or not admin_password or not admin_full_name:
            raise ValueError(
                "ADMIN bootstrap is enabled, but required env vars are missing: "
                "ADMIN_BOOTSTRAP_EMAIL, ADMIN_BOOTSTRAP_PASSWORD, ADMIN_BOOTSTRAP_FULL_NAME."
            )

        create_admin_user(
            db,
            email=admin_email,
            password=admin_password,
            full_name=admin_full_name,
            position=admin_position,
            department=admin_department,
        )
    finally:
        db.close()

if __name__ == "__main__":
    init_db()