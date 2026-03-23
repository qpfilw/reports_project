from __future__ import annotations
from tests.helpers import (
    create_project,
    create_report,
    create_report_type,
    create_template,
    launch_processing_task,
    login_headers,
    register_user,
    run_csv_export,
    upload_csv,
)

def test_user_cannot_access_foreign_project_artifacts(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]

    report_type = create_report_type(client, admin_headers, code="SEC_MONTHLY", name="Security Monthly")
    create_template(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
        code="sec_template",
    )
    project = create_project(
        client,
        admin_headers,
        owner_id=admin_user_id,
        name="Secret Project",
        code="SECRET001",
    )
    report = create_report(
        client,
        admin_headers,
        project_id=project["id"],
        report_type_id=report_type["id"],
        creator_id=admin_user_id,
        title="Secret Report",
    )
    good_csv = "id,name,date,amount,count\n1,Sales,2026-03-01,120000,15\n"
    upload = upload_csv(
        client,
        admin_headers,
        report_id=report["id"],
        filename="secret.csv",
        content=good_csv,
    )
    task = launch_processing_task(
        client,
        admin_headers,
        report_id=report["id"],
        report_upload_id=upload["id"],
    )
    export = run_csv_export(client, admin_headers, processing_task_id=task["id"])

    registered = register_user(
        client,
        email="outsider@example.com",
        full_name="Outside User",
    )
    outsider_id = registered["user"]["id"]
    approve_user = client.post(
        f"/api/v1/admin/users/{outsider_id}/approve",
        headers=admin_headers,
        json={"role_code": "viewer"},
    )
    assert approve_user.status_code == 200

    outsider_headers, _ = login_headers(client, "outsider@example.com", "UserPass123!")

    assert client.get(f"/api/v1/projects/{project['id']}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/uploads/{upload['id']}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/processing/tasks/{task['id']}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/results/by-task/{task['id']}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/exports/{export['id']}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/exports/{export['id']}/download", headers=outsider_headers).status_code == 403
