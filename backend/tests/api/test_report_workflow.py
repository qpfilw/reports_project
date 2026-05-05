from __future__ import annotations

from tests.helpers import (
    create_project,
    create_report,
    create_report_type,
    create_template,
    launch_processing_task,
    login_headers,
    upload_csv,
)

GOOD_CSV = "id,name,date,amount,count\n1,Sales,2026-03-01,120000,15\n2,Procurement,2026-03-02,83000,9\n"
DIRTY_CSV = "id,name,date,amount,count\n1,Sales,2026-03-01,120000,15\na,Procurement,,oops,9\n"


def _create_report_with_template(client, admin_headers, admin_user_id, *, suffix: str):
    report_type = create_report_type(
        client,
        admin_headers,
        code=f"WF_{suffix}",
        name=f"Workflow {suffix}",
    )
    template = create_template(
        client,
        admin_headers,
        report_type_id=report_type["id"],
        created_by=admin_user_id,
        code=f"workflow_template_{suffix.lower()}",
    )
    project = create_project(
        client,
        admin_headers,
        owner_id=admin_user_id,
        name=f"Workflow Project {suffix}",
        code=f"WFP{suffix}",
    )
    report = create_report(
        client,
        admin_headers,
        project_id=project["id"],
        report_type_id=report_type["id"],
        creator_id=admin_user_id,
        title=f"Workflow Report {suffix}",
        ml_template_id=template["id"],
    )
    return project, report_type, template, report


def test_report_review_approval_and_archive_workflow(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]
    _, _, _, report = _create_report_with_template(client, admin_headers, admin_user_id, suffix="APPROVE")

    upload = upload_csv(
        client,
        admin_headers,
        report_id=report["id"],
        filename="workflow.csv",
        content=GOOD_CSV,
    )
    task = launch_processing_task(
        client,
        admin_headers,
        report_id=report["id"],
        report_upload_id=upload["id"],
        ml_template_id=report["ml_template"]["id"] if report.get("ml_template") else None,
    )
    assert task["status"] == "success"

    review_response = client.post(
        f"/api/v1/reports/{report['id']}/submit-review",
        headers=admin_headers,
        json={"last_comment": "ready for review", "current_assignee_id": admin_user_id},
    )
    assert review_response.status_code == 200, review_response.text
    assert review_response.json()["status"] == "on_review"
    assert review_response.json()["current_assignee"]["id"] == admin_user_id

    invalid_approve_response = client.post(
        f"/api/v1/reports/{report['id']}/approve",
        headers=admin_headers,
        json={"last_comment": "cannot approve before approval step"},
    )
    assert invalid_approve_response.status_code in {400, 409}

    approval_response = client.post(
        f"/api/v1/reports/{report['id']}/submit-approval",
        headers=admin_headers,
        json={"last_comment": "review complete", "approver_id": admin_user_id},
    )
    assert approval_response.status_code == 200, approval_response.text
    assert approval_response.json()["status"] == "on_approval"
    assert approval_response.json()["approver"]["id"] == admin_user_id

    approve_response = client.post(
        f"/api/v1/reports/{report['id']}/approve",
        headers=admin_headers,
        json={"last_comment": "approved"},
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["status"] == "approved"
    assert approve_response.json()["approved_at"] is not None

    archive_response = client.patch(
        f"/api/v1/reports/{report['id']}/status",
        headers=admin_headers,
        json={"status": "archived", "last_comment": "archive after approval"},
    )
    assert archive_response.status_code == 200, archive_response.text
    assert archive_response.json()["status"] == "archived"
    assert archive_response.json()["is_archived"] is True


def test_failed_report_can_be_sent_to_rework_and_processed_again(client, admin_credentials):
    admin_headers, admin_login = login_headers(client, **admin_credentials)
    admin_user_id = admin_login["user"]["id"]
    _, _, _, report = _create_report_with_template(client, admin_headers, admin_user_id, suffix="REWORK")

    dirty_upload = upload_csv(
        client,
        admin_headers,
        report_id=report["id"],
        filename="dirty.csv",
        content=DIRTY_CSV,
    )
    failed_task = launch_processing_task(
        client,
        admin_headers,
        report_id=report["id"],
        report_upload_id=dirty_upload["id"],
    )
    assert failed_task["status"] == "failed"
    assert failed_task["report"]["status"] == "failed"

    rework_response = client.post(
        f"/api/v1/reports/{report['id']}/rework",
        headers=admin_headers,
        json={"last_comment": "fix source file"},
    )
    assert rework_response.status_code == 200, rework_response.text
    assert rework_response.json()["status"] == "rework"

    corrected_upload = upload_csv(
        client,
        admin_headers,
        report_id=report["id"],
        filename="corrected.csv",
        content=GOOD_CSV,
        comment="corrected upload",
    )
    assert corrected_upload["upload_version"] >= dirty_upload["upload_version"]

    successful_task = launch_processing_task(
        client,
        admin_headers,
        report_id=report["id"],
        report_upload_id=corrected_upload["id"],
    )
    assert successful_task["status"] == "success"
    assert successful_task["report"]["status"] == "processed"
