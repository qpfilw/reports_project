from __future__ import annotations

from tests.helpers import (
    add_project_member,
    create_approved_user,
    create_project,
    login_headers,
    update_project_member,
)


def test_project_owner_can_manage_members_and_archive_project(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]
    viewer_headers, viewer_login, _ = create_approved_user(
        client,
        admin_headers,
        email="project.viewer@example.com",
        role_code="viewer",
    )

    project = create_project(
        client,
        admin_headers,
        owner_id=admin_user_id,
        name="Members Project",
        code="MEMBERS001",
    )

    member = add_project_member(
        client,
        admin_headers,
        project_id=project["id"],
        user_id=viewer_login["user"]["id"],
        member_role="viewer",
    )
    assert member["access_status"] == "approved"
    assert member["member_role"] == "viewer"

    project_for_viewer = client.get(f"/api/v1/projects/{project['id']}", headers=viewer_headers)
    assert project_for_viewer.status_code == 200, project_for_viewer.text

    updated_member = update_project_member(
        client,
        admin_headers,
        project_id=project["id"],
        member_id=member["id"],
        member_role="editor",
    )
    assert updated_member["member_role"] == "editor"

    owner_membership = next(item for item in project["members"] if item["user_id"] == admin_user_id)
    bad_owner_update = client.patch(
        f"/api/v1/projects/{project['id']}/members/{owner_membership['id']}",
        headers=admin_headers,
        json={"member_role": "viewer"},
    )
    assert bad_owner_update.status_code == 400

    remove_response = client.delete(
        f"/api/v1/projects/{project['id']}/members/{member['id']}",
        headers=admin_headers,
    )
    assert remove_response.status_code == 200, remove_response.text

    project_for_removed_user = client.get(f"/api/v1/projects/{project['id']}", headers=viewer_headers)
    assert project_for_removed_user.status_code == 403

    archive_response = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers=admin_headers,
        json={"is_archived": True},
    )
    assert archive_response.status_code == 200, archive_response.text
    assert archive_response.json()["is_archived"] is True


def test_viewer_cannot_create_project_or_manage_members(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    viewer_headers, viewer_login, _ = create_approved_user(
        client,
        admin_headers,
        email="plain.viewer@example.com",
        role_code="viewer",
    )
    project = create_project(
        client,
        admin_headers,
        owner_id=admin_login["user"]["id"],
        name="Owner Only Project",
        code="OWNERONLY001",
    )

    create_response = client.post(
        "/api/v1/projects/",
        headers=viewer_headers,
        json={
            "name": "Forbidden Project",
            "code": "FORBIDDEN001",
            "description": "viewer should not create projects",
            "owner_id": viewer_login["user"]["id"],
        },
    )
    assert create_response.status_code == 403

    add_response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        headers=viewer_headers,
        json={
            "user_id": viewer_login["user"]["id"],
            "member_role": "viewer",
            "request_note": "should be denied",
        },
    )
    assert add_response.status_code == 403
