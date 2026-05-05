from __future__ import annotations

from tests.helpers import create_approved_user, login_headers, register_user


def test_approved_user_can_update_profile_and_change_password(client, admin_credentials):
    admin_headers, _ = login_headers(client, **admin_credentials)
    user_headers, login_payload, _ = create_approved_user(
        client,
        admin_headers,
        email="profile.operator@example.com",
        full_name="Profile Operator",
        role_code="operator",
    )

    update_response = client.patch(
        "/api/v1/auth/me",
        headers=user_headers,
        json={
            "email": "profile.operator.updated@example.com",
            "full_name": "Updated Operator",
            "position": "Senior Operator",
            "department": "Reporting",
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated_user = update_response.json()
    assert updated_user["id"] == login_payload["user"]["id"]
    assert updated_user["email"] == "profile.operator.updated@example.com"
    assert updated_user["full_name"] == "Updated Operator"
    assert updated_user["position"] == "Senior Operator"
    assert updated_user["department"] == "Reporting"
    assert updated_user["role"]["code"] == "operator"

    wrong_password_response = client.post(
        "/api/v1/auth/change-password",
        headers=user_headers,
        json={"current_password": "bad-password", "new_password": "NewUserPass123!"},
    )
    assert wrong_password_response.status_code == 400

    change_response = client.post(
        "/api/v1/auth/change-password",
        headers=user_headers,
        json={"current_password": "UserPass123!", "new_password": "NewUserPass123!"},
    )
    assert change_response.status_code == 200, change_response.text

    old_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "profile.operator.updated@example.com", "password": "UserPass123!"},
    )
    assert old_login_response.status_code == 401

    new_headers, new_login_payload = login_headers(
        client,
        "profile.operator.updated@example.com",
        "NewUserPass123!",
    )
    assert new_headers["Authorization"].startswith("Bearer ")
    assert new_login_payload["user"]["full_name"] == "Updated Operator"


def test_profile_update_rejects_duplicate_email(client, admin_credentials):
    admin_headers, _ = login_headers(client, **admin_credentials)
    first_headers, _, _ = create_approved_user(
        client,
        admin_headers,
        email="duplicate.first@example.com",
        role_code="operator",
    )
    register_user(
        client,
        email="duplicate.second@example.com",
        full_name="Duplicate Second",
    )

    duplicate_response = client.patch(
        "/api/v1/auth/me",
        headers=first_headers,
        json={"email": "duplicate.second@example.com"},
    )
    assert duplicate_response.status_code == 409


def test_blocked_user_cannot_login_after_admin_block(client, admin_credentials):
    admin_headers, _ = login_headers(client, **admin_credentials)
    _, _, approved_user = create_approved_user(
        client,
        admin_headers,
        email="blocked.user@example.com",
        role_code="viewer",
    )

    block_response = client.post(
        f"/api/v1/admin/users/{approved_user['id']}/block",
        headers=admin_headers,
        json={"reason": "Security test"},
    )
    assert block_response.status_code == 200, block_response.text
    assert block_response.json()["is_blocked"] is True

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "blocked.user@example.com", "password": "UserPass123!"},
    )
    assert login_response.status_code == 403
