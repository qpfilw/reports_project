from __future__ import annotations
from io import BytesIO
from typing import Any
from fastapi.testclient import TestClient

def login(client: TestClient, email: str, password: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()

def bearer_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}

def login_headers(client: TestClient, email: str, password: str) -> tuple[dict[str, str], dict[str, Any]]:
    payload = login(client, email, password)
    access_token = payload["tokens"]["access_token"]
    return bearer_headers(access_token), payload

def register_user(
    client: TestClient,
    *,
    email: str,
    password: str = "UserPass123!",
    full_name: str = "Test User",
    position: str = "Engineer",
    department: str = "QA",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "position": position,
            "department": department,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()

def create_project(client: TestClient, headers: dict[str, str], *, owner_id: int, name: str, code: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/projects/",
        headers=headers,
        json={
            "name": name,
            "code": code,
            "description": f"Project {name}",
            "owner_id": owner_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()

def create_report_type(client: TestClient, headers: dict[str, str], *, code: str, name: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/report-types/",
        headers=headers,
        json={
            "code": code,
            "name": name,
            "description": f"Report type {name}",
            "schema_version": "1.0",
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()

def create_template(
    client: TestClient,
    headers: dict[str, str],
    *,
    report_type_id: int,
    created_by: int,
    code: str = "test_template",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/templates/",
        headers=headers,
        json={
            "code": code,
            "name": "Template for tests",
            "description": "Template used in automated tests",
            "template_type": "classification",
            "target_report_type_id": report_type_id,
            "config_json": {
                "target_fields": ["id", "name", "date", "amount", "count"],
                "field_aliases": {
                    "id": ["id", "код", "номер", "code"],
                    "name": ["name", "наименование", "название"],
                    "date": ["date", "дата", "period"],
                    "amount": ["amount", "sum", "total", "сумма"],
                    "count": ["count", "qty", "количество"],
                },
            },
            "metrics_json": {},
            "version": "1.0",
            "is_default": True,
            "is_active": True,
            "created_by": created_by,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()

def create_report(
    client: TestClient,
    headers: dict[str, str],
    *,
    project_id: int,
    report_type_id: int,
    creator_id: int,
    title: str = "March Report",
    ml_template_id: int | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/reports/",
        headers=headers,
        json={
            "project_id": project_id,
            "report_type_id": report_type_id,
            "title": title,
            "description": "Automated test report",
            "report_period_start": "2026-03-01",
            "report_period_end": "2026-03-31",
            "creator_id": creator_id,
            "current_assignee_id": None,
            "approver_id": None,
            "ml_template_id": ml_template_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()

def upload_csv(
    client: TestClient,
    headers: dict[str, str],
    *,
    report_id: int,
    filename: str,
    content: str,
    comment: str = "test upload",
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/reports/{report_id}/uploads/file",
        headers=headers,
        data={"comment": comment},
        files={"file": (filename, BytesIO(content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 201, response.text
    return response.json()

def launch_processing_task(
    client: TestClient,
    headers: dict[str, str],
    *,
    report_id: int,
    report_upload_id: int,
    ml_template_id: int | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/processing/tasks",
        headers=headers,
        json={
            "report_id": report_id,
            "report_upload_id": report_upload_id,
            "ml_template_id": ml_template_id,
            "priority": 5,
            "params_json": {},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()

def run_csv_export(client: TestClient, headers: dict[str, str], *, processing_task_id: int) -> dict[str, Any]:
    response = client.post(
        "/api/v1/exports/run",
        headers=headers,
        json={
            "processing_task_id": processing_task_id,
            "report_id": None,
            "dashboard_id": None,
            "format": "csv",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()

def approve_registered_user(
    client: TestClient,
    admin_headers: dict[str, str],
    *,
    user_id: int,
    role_code: str = "viewer",
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/admin/users/{user_id}/approve",
        headers=admin_headers,
        json={"role_code": role_code},
    )
    assert response.status_code == 200, response.text
    return response.json()


def create_approved_user(
    client: TestClient,
    admin_headers: dict[str, str],
    *,
    email: str,
    password: str = "UserPass123!",
    full_name: str = "Approved User",
    role_code: str = "viewer",
) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
    registered = register_user(
        client,
        email=email,
        password=password,
        full_name=full_name,
    )
    approved = approve_registered_user(
        client,
        admin_headers,
        user_id=registered["user"]["id"],
        role_code=role_code,
    )
    headers, login_payload = login_headers(client, email, password)
    return headers, login_payload, approved


def add_project_member(
    client: TestClient,
    headers: dict[str, str],
    *,
    project_id: int,
    user_id: int,
    member_role: str = "viewer",
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=headers,
        json={
            "user_id": user_id,
            "member_role": member_role,
            "request_note": "Added by automated test",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def update_project_member(
    client: TestClient,
    headers: dict[str, str],
    *,
    project_id: int,
    member_id: int,
    member_role: str,
) -> dict[str, Any]:
    response = client.patch(
        f"/api/v1/projects/{project_id}/members/{member_id}",
        headers=headers,
        json={"member_role": member_role, "review_note": "Updated by automated test"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def create_notification(
    client: TestClient,
    headers: dict[str, str],
    *,
    user_id: int,
    title: str = "Test notification",
    message: str = "Notification created by automated test",
    type_: str = "system_alert",
    project_id: int | None = None,
    report_id: int | None = None,
    processing_task_id: int | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/notifications/",
        headers=headers,
        json={
            "user_id": user_id,
            "project_id": project_id,
            "report_id": report_id,
            "processing_task_id": processing_task_id,
            "type": type_,
            "title": title,
            "message": message,
            "payload_json": {"source": "pytest"},
            "is_read": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_dashboard(
    client: TestClient,
    headers: dict[str, str],
    *,
    project_id: int,
    owner_id: int,
    name: str = "QA dashboard",
    report_id: int | None = None,
    normalized_dataset_id: int | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/analytics/dashboards",
        headers=headers,
        json={
            "project_id": project_id,
            "report_id": report_id,
            "normalized_dataset_id": normalized_dataset_id,
            "owner_id": owner_id,
            "name": name,
            "description": "Dashboard created by automated test",
            "dashboard_type": "personal",
            "source_type": "project_aggregate",
            "config_json": {"widgets": ["reports", "tasks", "exports"]},
            "filters_json": {"period": "month"},
            "layout_json": {"columns": 3},
            "metrics_json": {"reports": True},
            "is_shared": False,
            "is_default": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_processing_script(
    client: TestClient,
    headers: dict[str, str],
    *,
    report_type_id: int | None,
    created_by: int,
    code: str = "expense_control_script",
    script_code: str | None = None,
) -> dict[str, Any]:
    script_code = script_code or '''def process(context):
    rows = context.get("rows") or []

    for row in rows:
        total = float(row.get("Итого с НДС") or row.get("amount") or 0)
        status = str(row.get("Статус оплаты") or "").strip()

        if status == "Ожидает оплаты" and total >= 300000:
            row["Результат контроля"] = "Требует срочного контроля"
            row["Уровень риска"] = "Высокий"
            row["Требуется согласование"] = "Да"
        elif status == "Ожидает оплаты" and total >= 100000:
            row["Результат контроля"] = "Требует контроля"
            row["Уровень риска"] = "Средний"
            row["Требуется согласование"] = "Да"
        else:
            row["Результат контроля"] = "Без замечаний"
            row["Уровень риска"] = "Низкий"
            row["Требуется согласование"] = "Нет"

    return {
        "rows": rows,
        "summary": {
            "script": "expense_control",
            "processed_rows": len(rows),
        },
        "warnings": [],
    }
'''
    response = client.post(
        "/api/v1/processing-scripts/",
        headers=headers,
        json={
            "code": code,
            "name": "Expense control script",
            "description": "Adds business control columns",
            "target_report_type_id": report_type_id,
            "script_code": script_code,
            "version": "1.0",
            "is_default": True,
            "is_active": True,
            "created_by": created_by,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
