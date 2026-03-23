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