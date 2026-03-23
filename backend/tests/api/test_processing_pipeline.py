from __future__ import annotations
from tests.helpers import (
    create_project,
    create_report,
    create_report_type,
    create_template,
    launch_processing_task,
    login_headers,
    run_csv_export,
    upload_csv,
)

def test_happy_path_processing_ml_and_export(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]

    report_type = create_report_type(client, admin_headers, code="FIN_MONTHLY", name="Financial Monthly")
    template = create_template(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
        code="fin_template",
    )
    project = create_project(
        client,
        admin_headers,
        owner_id=admin_user_id,
        name="Processing Project",
        code="PROC001",
    )
    report = create_report(
        client,
        admin_headers,
        project_id=project["id"],
        report_type_id=report_type["id"],
        creator_id=admin_user_id,
        title="March Financial Report",
    )

    good_csv = "id,name,date,amount,count\n1,Sales,2026-03-01,120000,15\n2,Procurement,2026-03-02,83000,9\n3,Logistics,2026-03-03,91000,11\n"
    upload = upload_csv(
        client,
        admin_headers,
        report_id=report["id"],
        filename="good.csv",
        content=good_csv,
    )

    prediction_response = client.get(
        f"/api/v1/ml/uploads/{upload['id']}/template-prediction",
        headers=admin_headers,
    )
    assert prediction_response.status_code == 200, prediction_response.text
    prediction_json = prediction_response.json()
    assert prediction_json["best_match"]["template_id"] == template["id"]
    assert prediction_json["best_match"]["confidence"] > 0.5
    assert prediction_json["candidates"]

    task = launch_processing_task(
        client,
        admin_headers,
        report_id=report["id"],
        report_upload_id=upload["id"],
    )
    assert task["status"] == "success"
    assert task["error_count"] == 0
    assert task["report"]["status"] == "processed"

    pipeline_response = client.get(
        f"/api/v1/ml/tasks/{task['id']}/pipeline-result",
        headers=admin_headers,
    )
    assert pipeline_response.status_code == 200, pipeline_response.text
    pipeline_json = pipeline_response.json()
    assert pipeline_json["selected_template"]["id"] == template["id"]
    assert len(pipeline_json["column_matches"]) == 5
    assert pipeline_json["mapping_confirmation_required"] is False
    assert pipeline_json["diagnostics"]["headers"] == ["id", "name", "date", "amount", "count"]

    result_response = client.get(f"/api/v1/results/by-task/{task['id']}", headers=admin_headers)
    assert result_response.status_code == 200, result_response.text
    assert result_response.json()["rows_count"] == 3

    export = run_csv_export(client, admin_headers, processing_task_id=task["id"])
    download_response = client.get(f"/api/v1/exports/{export['id']}/download", headers=admin_headers)
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("text/csv")

def test_dirty_file_fails_and_export_is_blocked(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]

    report_type = create_report_type(client, admin_headers, code="OPS_MONTHLY", name="Operations Monthly")
    create_template(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
        code="ops_template",
    )
    project = create_project(
        client,
        admin_headers,
        owner_id=admin_user_id,
        name="Negative Project",
        code="NEG001",
    )
    report = create_report(
        client,
        admin_headers,
        project_id=project["id"],
        report_type_id=report_type["id"],
        creator_id=admin_user_id,
        title="Broken Report",
    )

    dirty_csv = "id,name,date,amount,count\n1,Sales,2026-03-01,120000,15\na,Procurement,,oops,9\n3,Logistics,2026-03-03,91000,\n"
    upload = upload_csv(
        client,
        admin_headers,
        report_id=report["id"],
        filename="dirty.csv",
        content=dirty_csv,
    )

    task = launch_processing_task(
        client,
        admin_headers,
        report_id=report["id"],
        report_upload_id=upload["id"],
    )
    assert task["status"] == "failed"
    assert task["error_count"] > 0
    assert task["report"]["status"] == "failed"

    errors_response = client.get(f"/api/v1/processing/tasks/{task['id']}/errors", headers=admin_headers)
    assert errors_response.status_code == 200
    assert errors_response.json()

    result_response = client.get(f"/api/v1/results/by-task/{task['id']}", headers=admin_headers)
    assert result_response.status_code == 404

    export_response = client.post(
        "/api/v1/exports/run",
        headers=admin_headers,
        json={
            "processing_task_id": task["id"],
            "report_id": None,
            "dashboard_id": None,
            "format": "csv",
        },
    )
    assert export_response.status_code == 409
