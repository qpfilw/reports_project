from __future__ import annotations

from app.utils.storage import read_json
from tests.helpers import (
    create_processing_script,
    create_project,
    create_report,
    create_report_type,
    create_template,
    launch_processing_task,
    login_headers,
    upload_csv,
)

EXPENSE_CSV = """ID операции,Дата операции,Код филиала,Филиал,Количество,Итого с НДС,Статус оплаты
1,01.03.2026,1001,Москва,2,350000,Ожидает оплаты
2,02.03.2026,1002,Казань,1,50000,Оплачено
"""


def test_processing_script_validation_endpoint_requires_process_entrypoint(client, admin_credentials):
    admin_headers, _ = login_headers(client, **admin_credentials)

    invalid_response = client.post(
        "/api/v1/processing-scripts/validate",
        headers=admin_headers,
        json={"script_code": "def process_row(row):\n    return row"},
    )
    assert invalid_response.status_code == 200, invalid_response.text
    payload = invalid_response.json()
    assert payload["is_valid"] is False
    assert "process(context)" in payload["error"]

    valid_response = client.post(
        "/api/v1/processing-scripts/validate",
        headers=admin_headers,
        json={
            "script_code": (
                "def process(context):\n"
                "    rows = context.get('rows') or []\n"
                "    for row in rows:\n"
                "        row['Проверено скриптом'] = 'Да'\n"
                "    return {'rows': rows, 'summary': {}, 'warnings': []}\n"
            )
        },
    )
    assert valid_response.status_code == 200, valid_response.text
    valid_payload = valid_response.json()
    assert valid_payload["is_valid"] is True
    assert "Проверено скриптом" in valid_payload["added_columns"]


def test_processing_script_adds_columns_to_normalized_result(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]

    report_type = create_report_type(
        client,
        admin_headers,
        code="SCRIPT_EXPENSE_TYPE",
        name="Script expense type",
    )
    script = create_processing_script(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
    )
    template = create_template(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
        code="script_template",
    )
    update_template_response = client.patch(
        f"/api/v1/templates/{template['id']}",
        headers=admin_headers,
        json={"processing_script_id": script["id"]},
    )
    assert update_template_response.status_code == 200, update_template_response.text

    project = create_project(
        client,
        admin_headers,
        owner_id=admin_user_id,
        name="Script Project",
        code="SCRIPT001",
    )
    report = create_report(
        client,
        admin_headers,
        project_id=project["id"],
        report_type_id=report_type["id"],
        creator_id=admin_user_id,
        title="Script enriched report",
        ml_template_id=template["id"],
    )
    upload = upload_csv(
        client,
        admin_headers,
        report_id=report["id"],
        filename="expenses.csv",
        content=EXPENSE_CSV,
    )
    task = launch_processing_task(
        client,
        admin_headers,
        report_id=report["id"],
        report_upload_id=upload["id"],
        ml_template_id=template["id"],
    )
    assert task["status"] == "success", task

    result_response = client.get(f"/api/v1/results/by-task/{task['id']}", headers=admin_headers)
    assert result_response.status_code == 200, result_response.text
    result = result_response.json()

    normalized_payload = read_json(result["data_location"])
    rows = normalized_payload["rows"]
    assert rows[0]["Результат контроля"] == "Требует срочного контроля"
    assert rows[0]["Уровень риска"] == "Высокий"
    assert rows[0]["Требуется согласование"] == "Да"
    assert rows[1]["Результат контроля"] == "Без замечаний"

    schema_columns = normalized_payload["schema_json"]["columns"]
    assert "Результат контроля" in schema_columns
    assert "Уровень риска" in schema_columns
    assert "Требуется согласование" in schema_columns

    summary = normalized_payload["summary_json"]
    assert summary["script_processing"]["added_columns_count"] == 3
    assert set(summary["script_processing"]["added_columns"]) >= {
        "Результат контроля",
        "Уровень риска",
        "Требуется согласование",
    }
    assert summary["control_summary"]["risk_high"] == 1
    assert summary["control_summary"]["requires_approval"] == 1
