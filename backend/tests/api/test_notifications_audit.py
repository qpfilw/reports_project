from __future__ import annotations

from tests.helpers import create_approved_user, create_notification, create_project, login_headers


def test_notification_visibility_and_mark_as_read(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    first_headers, first_login, _ = create_approved_user(
        client,
        admin_headers,
        email="notification.first@example.com",
        role_code="operator",
    )
    second_headers, _, _ = create_approved_user(
        client,
        admin_headers,
        email="notification.second@example.com",
        role_code="viewer",
    )
    project = create_project(
        client,
        admin_headers,
        owner_id=admin_login["user"]["id"],
        name="Notification Project",
        code="NOTIFY001",
    )
    notification = create_notification(
        client,
        admin_headers,
        user_id=first_login["user"]["id"],
        project_id=project["id"],
        title="Processing finished",
        message="Report processing has been completed.",
        type_="task_completed",
    )

    first_list_response = client.get("/api/v1/notifications/", headers=first_headers)
    assert first_list_response.status_code == 200, first_list_response.text
    assert [item["id"] for item in first_list_response.json()] == [notification["id"]]

    second_detail_response = client.get(
        f"/api/v1/notifications/{notification['id']}",
        headers=second_headers,
    )
    assert second_detail_response.status_code == 403

    read_response = client.post(
        f"/api/v1/notifications/{notification['id']}/read",
        headers=first_headers,
    )
    assert read_response.status_code == 200, read_response.text
    assert read_response.json()["is_read"] is True
    assert read_response.json()["read_at"] is not None


def test_audit_is_admin_only_and_records_key_actions(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    viewer_headers, _, _ = create_approved_user(
        client,
        admin_headers,
        email="audit.viewer@example.com",
        role_code="viewer",
    )
    create_project(
        client,
        admin_headers,
        owner_id=admin_login["user"]["id"],
        name="Audit Project",
        code="AUDIT001",
    )

    forbidden_response = client.get("/api/v1/audit/", headers=viewer_headers)
    assert forbidden_response.status_code == 403

    audit_response = client.get("/api/v1/audit/", headers=admin_headers)
    assert audit_response.status_code == 200, audit_response.text
    logs = audit_response.json()
    assert logs
    assert any(item["action"] == "create" and item["entity_type"] == "project" for item in logs)
    assert any(item["action"] == "login" and item["entity_type"] == "user" for item in logs)

    detail_response = client.get(f"/api/v1/audit/{logs[0]['id']}", headers=admin_headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["id"] == logs[0]["id"]
