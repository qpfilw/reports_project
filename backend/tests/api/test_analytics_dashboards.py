from __future__ import annotations

from tests.helpers import create_dashboard, create_project, create_report_type, login_headers


def test_analytics_overview_and_dashboard_crud(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]
    project = create_project(
        client,
        admin_headers,
        owner_id=admin_user_id,
        name="Analytics Project",
        code="ANALYTICS001",
    )
    create_report_type(
        client,
        admin_headers,
        code="ANALYTICS_TYPE",
        name="Analytics Type",
    )

    overview_response = client.get("/api/v1/analytics/overview", headers=admin_headers)
    assert overview_response.status_code == 200, overview_response.text
    overview = overview_response.json()
    assert overview["total_reports"] == 0
    assert overview["total_tasks"] == 0
    assert overview["total_exports"] == 0
    assert any(item["key"] == "dashboards" for item in overview["metrics"])

    dashboard = create_dashboard(
        client,
        admin_headers,
        project_id=project["id"],
        owner_id=admin_user_id,
        name="Executive dashboard",
    )
    assert dashboard["name"] == "Executive dashboard"
    assert dashboard["config_json"]["widgets"] == ["reports", "tasks", "exports"]

    duplicate_response = client.post(
        "/api/v1/analytics/dashboards",
        headers=admin_headers,
        json={
            "project_id": project["id"],
            "owner_id": admin_user_id,
            "name": "Executive dashboard",
            "description": "duplicate dashboard",
            "dashboard_type": "personal",
            "source_type": "project_aggregate",
            "config_json": {},
            "filters_json": {},
            "layout_json": {},
            "metrics_json": {},
            "is_shared": False,
            "is_default": False,
        },
    )
    assert duplicate_response.status_code == 409

    update_response = client.patch(
        f"/api/v1/analytics/dashboards/{dashboard['id']}",
        headers=admin_headers,
        json={
            "name": "Updated dashboard",
            "is_default": True,
            "layout_json": {"columns": 2, "compact": True},
        },
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["name"] == "Updated dashboard"
    assert update_response.json()["is_default"] is True
    assert update_response.json()["layout_json"]["compact"] is True

    list_response = client.get("/api/v1/analytics/dashboards", headers=admin_headers)
    assert list_response.status_code == 200, list_response.text
    assert [item["id"] for item in list_response.json()] == [dashboard["id"]]

    delete_response = client.delete(f"/api/v1/analytics/dashboards/{dashboard['id']}", headers=admin_headers)
    assert delete_response.status_code == 200, delete_response.text

    get_deleted_response = client.get(f"/api/v1/analytics/dashboards/{dashboard['id']}", headers=admin_headers)
    assert get_deleted_response.status_code == 404
