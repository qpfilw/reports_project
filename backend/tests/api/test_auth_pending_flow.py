from __future__ import annotations
from tests.helpers import login_headers, register_user


def test_pending_user_has_limited_access(client, admin_credentials):
    admin_headers, _ = login_headers(client, **admin_credentials)

    register_response = register_user(
        client,
        email="pending.user@example.com",
        full_name="Pending User",
    )
    pending_headers, pending_login = login_headers(client, "pending.user@example.com", "UserPass123!")

    assert pending_login["user"]["role"]["code"] == "pending"

    me_response = client.get("/api/v1/auth/me", headers=pending_headers)
    assert me_response.status_code == 200
    assert me_response.json()["role"]["code"] == "pending"

    projects_response = client.get("/api/v1/projects/", headers=pending_headers)
    assert projects_response.status_code == 403
    assert "pending approval" in projects_response.json()["detail"].lower()

    password_response = client.post(
        "/api/v1/auth/change-password",
        headers=pending_headers,
        json={
            "current_password": "UserPass123!",
            "new_password": "UserPass456!",
        },
    )
    assert password_response.status_code == 403

    pending_users_response = client.get("/api/v1/admin/pending-users", headers=admin_headers)
    assert pending_users_response.status_code == 200
    emails = {item["email"] for item in pending_users_response.json()}
    assert register_response["user"]["email"] in emails
