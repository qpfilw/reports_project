from __future__ import annotations

from tests.helpers import create_report_type, create_template, login_headers


def test_report_type_create_update_and_duplicate_code_validation(client, admin_credentials):
    admin_headers, _ = login_headers(client, **admin_credentials)
    report_type = create_report_type(
        client,
        admin_headers,
        code="TYPE_DUPLICATE",
        name="Initial type",
    )

    duplicate_response = client.post(
        "/api/v1/report-types/",
        headers=admin_headers,
        json={
            "code": "TYPE_DUPLICATE",
            "name": "Duplicate type",
            "description": "should not be created",
            "schema_version": "1.0",
            "is_active": True,
        },
    )
    assert duplicate_response.status_code == 409

    update_response = client.patch(
        f"/api/v1/report-types/{report_type['id']}",
        headers=admin_headers,
        json={"name": "Updated report type", "is_active": False},
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["name"] == "Updated report type"
    assert update_response.json()["is_active"] is False


def test_default_template_switches_previous_default_for_same_report_type(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]
    report_type = create_report_type(
        client,
        admin_headers,
        code="TYPE_TEMPLATE_DEFAULT",
        name="Template default type",
    )
    first_template = create_template(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
        code="default_template_one",
    )
    second_template = create_template(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
        code="default_template_two",
    )

    first_detail_response = client.get(
        f"/api/v1/templates/{first_template['id']}",
        headers=admin_headers,
    )
    second_detail_response = client.get(
        f"/api/v1/templates/{second_template['id']}",
        headers=admin_headers,
    )
    assert first_detail_response.status_code == 200, first_detail_response.text
    assert second_detail_response.status_code == 200, second_detail_response.text
    assert first_detail_response.json()["is_default"] is False
    assert second_detail_response.json()["is_default"] is True


def test_template_rejects_unknown_report_type_and_duplicate_code_version(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]
    report_type = create_report_type(
        client,
        admin_headers,
        code="TYPE_TEMPLATE_VALIDATE",
        name="Template validation type",
    )
    create_template(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
        code="unique_template_code",
    )

    duplicate_response = client.post(
        "/api/v1/templates/",
        headers=admin_headers,
        json={
            "code": "unique_template_code",
            "name": "Duplicate template",
            "description": "Duplicate code and version",
            "template_type": "classification",
            "target_report_type_id": report_type["id"],
            "config_json": {},
            "metrics_json": {},
            "version": "1.0",
            "is_default": False,
            "is_active": True,
            "created_by": admin_user_id,
        },
    )
    assert duplicate_response.status_code == 409

    unknown_report_type_response = client.post(
        "/api/v1/templates/",
        headers=admin_headers,
        json={
            "code": "unknown_report_type_template",
            "name": "Unknown report type template",
            "description": "Target report type does not exist",
            "template_type": "classification",
            "target_report_type_id": 999999,
            "config_json": {},
            "metrics_json": {},
            "version": "1.0",
            "is_default": False,
            "is_active": True,
            "created_by": admin_user_id,
        },
    )
    assert unknown_report_type_response.status_code == 404
