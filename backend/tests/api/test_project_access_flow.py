from __future__ import annotations
from tests.helpers import create_project, login_headers, register_user

def test_admin_approval_and_project_access_request_flow(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]

    project = create_project(
        client,
        admin_headers,
        owner_id=admin_user_id,
        name="Access Project",
        code="ACCESS001",
    )
    project_id = project["id"]

    registered = register_user(
        client,
        email="viewer.user@example.com",
        full_name="Viewer User",
    )
    user_id = registered["user"]["id"]

    approve_response = client.post(
        f"/api/v1/admin/users/{user_id}/approve",
        headers=admin_headers,
        json={"role_code": "viewer"},
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["role"]["code"] == "viewer"

    viewer_headers, viewer_login = login_headers(client, "viewer.user@example.com", "UserPass123!")
    assert viewer_login["user"]["role"]["code"] == "viewer"

    list_projects_response = client.get("/api/v1/projects/", headers=viewer_headers)
    assert list_projects_response.status_code == 200
    project_ids = {item["id"] for item in list_projects_response.json()}
    assert project_id in project_ids

    project_detail_forbidden = client.get(f"/api/v1/projects/{project_id}", headers=viewer_headers)
    assert project_detail_forbidden.status_code == 403

    request_response = client.post(
        f"/api/v1/projects/{project_id}/access-request",
        headers=viewer_headers,
        json={"member_role": "viewer", "request_note": "Need access for review"},
    )
    assert request_response.status_code == 201, request_response.text
    member_id = request_response.json()["id"]
    assert request_response.json()["access_status"] == "requested"

    pending_requests = client.get("/api/v1/admin/project-access-requests", headers=admin_headers)
    assert pending_requests.status_code == 200
    assert any(item["id"] == member_id for item in pending_requests.json())

    approve_access = client.post(
        f"/api/v1/admin/project-access-requests/{member_id}/approve",
        headers=admin_headers,
        json={"member_role": "viewer", "review_note": "Approved in tests"},
    )
    assert approve_access.status_code == 200, approve_access.text
    assert approve_access.json()["access_status"] == "approved"

    project_detail = client.get(f"/api/v1/projects/{project_id}", headers=viewer_headers)
    assert project_detail.status_code == 200
    assert project_detail.json()["id"] == project_id
