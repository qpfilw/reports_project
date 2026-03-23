from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_approved_user, require_manager_user
from app.core.access import (
    apply_project_scope,
    ensure_project_owner_or_admin,
    ensure_project_read_access,
    get_project_membership,
    get_project_or_404,
    is_admin,
)
from app.models.enums import ProjectAccessStatusEnum, ProjectMemberRoleEnum
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.common import MessageSchema
from app.schemas.project import (
    ProjectAccessRequestCreate,
    ProjectAccessReviewRequest,
    ProjectCreate,
    ProjectDetailRead,
    ProjectMemberCreate,
    ProjectMemberDetailRead,
    ProjectMemberUpdate,
    ProjectRead,
    ProjectUpdate,
)

router = APIRouter(dependencies=[Depends(require_approved_user)])


def _get_project_detail_or_404(db: Session, project_id: int) -> Project:
    stmt = (
        select(Project)
        .options(
            selectinload(Project.owner),
            selectinload(Project.members).selectinload(ProjectMember.user),
            selectinload(Project.members).selectinload(ProjectMember.creator),
            selectinload(Project.members).selectinload(ProjectMember.reviewer),
        )
        .where(Project.id == project_id)
    )
    project = db.scalar(stmt)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def _get_member_detail_or_404(db: Session, member_id: int) -> ProjectMember:
    stmt = (
        select(ProjectMember)
        .options(
            selectinload(ProjectMember.user),
            selectinload(ProjectMember.creator),
            selectinload(ProjectMember.reviewer),
        )
        .where(ProjectMember.id == member_id)
    )
    member = db.scalar(stmt)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found.")
    return member


@router.get("/", response_model=list[ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> list[Project]:
    stmt = select(Project).order_by(Project.id)
    return list(db.scalars(stmt).all())


@router.get("/{project_id}", response_model=ProjectDetailRead)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> Project:
    ensure_project_read_access(db, project_id=project_id, current_user=current_user)
    return _get_project_detail_or_404(db, project_id)


@router.get("/{project_id}/my-access", response_model=ProjectMemberDetailRead)
def get_my_project_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> ProjectMember:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    membership = get_project_membership(db, project_id=project_id, user_id=current_user.id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project access request was not found.")
    return _get_member_detail_or_404(db, membership.id)


@router.post("/", response_model=ProjectDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager_user)])
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> Project:
    owner = db.get(User, payload.owner_id)
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found.")

    if not is_admin(current_user) and payload.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an administrator can create a project for another owner.",
        )

    existing_code = db.scalar(select(Project).where(Project.code == payload.code))
    if existing_code is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project code already exists.")

    existing_name = db.scalar(
        select(Project).where(
            Project.owner_id == payload.owner_id,
            Project.name == payload.name,
        )
    )
    if existing_name is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project name already exists for this owner.")

    project = Project(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        owner_id=payload.owner_id,
    )
    db.add(project)
    db.flush()

    owner_member = ProjectMember(
        project_id=project.id,
        user_id=payload.owner_id,
        member_role=ProjectMemberRoleEnum.OWNER,
        access_status=ProjectAccessStatusEnum.APPROVED,
        added_by=current_user.id,
        requested_at=datetime.now(timezone.utc),
        reviewed_by=current_user.id,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(owner_member)

    db.commit()
    db.refresh(project)
    return _get_project_detail_or_404(db, project.id)


@router.patch("/{project_id}", response_model=ProjectDetailRead, dependencies=[Depends(require_manager_user)])
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> Project:
    project = ensure_project_owner_or_admin(db, project_id=project_id, current_user=current_user)

    data = payload.model_dump(exclude_unset=True)

    if "code" in data:
        existing = db.scalar(select(Project).where(Project.code == data["code"], Project.id != project_id))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project code already exists.")

    if "name" in data:
        existing = db.scalar(
            select(Project).where(
                Project.owner_id == project.owner_id,
                Project.name == data["name"],
                Project.id != project_id,
            )
        )
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project name already exists for this owner.")

    for field, value in data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return _get_project_detail_or_404(db, project.id)


@router.get("/{project_id}/members", response_model=list[ProjectMemberDetailRead])
def list_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> list[ProjectMember]:
    ensure_project_read_access(db, project_id=project_id, current_user=current_user)

    stmt = (
        select(ProjectMember)
        .options(
            selectinload(ProjectMember.user),
            selectinload(ProjectMember.creator),
            selectinload(ProjectMember.reviewer),
        )
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.id)
    )
    project = get_project_or_404(db, project_id)
    if not is_admin(current_user) and project.owner_id != current_user.id:
        stmt = stmt.where(
            (ProjectMember.access_status == ProjectAccessStatusEnum.APPROVED)
            | (ProjectMember.user_id == current_user.id)
        )
    return list(db.scalars(stmt).all())


@router.post("/{project_id}/access-request", response_model=ProjectMemberDetailRead, status_code=status.HTTP_201_CREATED)
def request_project_access(
    project_id: int,
    payload: ProjectAccessRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> ProjectMember:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if project.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project owner already has access to the project.",
        )

    membership = get_project_membership(db, project_id=project_id, user_id=current_user.id)
    if membership is not None and membership.access_status == ProjectAccessStatusEnum.APPROVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have approved access to this project.")

    if membership is None:
        membership = ProjectMember(
            project_id=project_id,
            user_id=current_user.id,
            member_role=payload.member_role,
            access_status=ProjectAccessStatusEnum.REQUESTED,
            requested_at=datetime.now(timezone.utc),
            request_note=payload.request_note,
        )
        db.add(membership)
    else:
        membership.member_role = payload.member_role
        membership.access_status = ProjectAccessStatusEnum.REQUESTED
        membership.requested_at = datetime.now(timezone.utc)
        membership.request_note = payload.request_note
        membership.reviewed_by = None
        membership.reviewed_at = None
        membership.review_note = None

    db.commit()
    db.refresh(membership)
    return _get_member_detail_or_404(db, membership.id)


@router.get("/{project_id}/access-requests", response_model=list[ProjectMemberDetailRead])
def list_project_access_requests(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> list[ProjectMember]:
    ensure_project_owner_or_admin(db, project_id=project_id, current_user=current_user)
    stmt = (
        select(ProjectMember)
        .options(
            selectinload(ProjectMember.user),
            selectinload(ProjectMember.creator),
            selectinload(ProjectMember.reviewer),
        )
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.access_status == ProjectAccessStatusEnum.REQUESTED,
        )
        .order_by(ProjectMember.requested_at.desc(), ProjectMember.id.desc())
    )
    return list(db.scalars(stmt).all())


@router.post("/{project_id}/access-requests/{member_id}/approve", response_model=ProjectMemberDetailRead, dependencies=[Depends(require_manager_user)])
def approve_project_access_request(
    project_id: int,
    member_id: int,
    payload: ProjectAccessReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> ProjectMember:
    ensure_project_owner_or_admin(db, project_id=project_id, current_user=current_user)
    member = db.get(ProjectMember, member_id)
    if member is None or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found.")

    member.access_status = ProjectAccessStatusEnum.APPROVED
    if payload.member_role is not None:
        member.member_role = payload.member_role
    member.reviewed_by = current_user.id
    member.reviewed_at = datetime.now(timezone.utc)
    member.review_note = payload.review_note
    if member.added_by is None:
        member.added_by = current_user.id

    db.commit()
    db.refresh(member)
    return _get_member_detail_or_404(db, member.id)


@router.post("/{project_id}/access-requests/{member_id}/reject", response_model=ProjectMemberDetailRead, dependencies=[Depends(require_manager_user)])
def reject_project_access_request(
    project_id: int,
    member_id: int,
    payload: ProjectAccessReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> ProjectMember:
    ensure_project_owner_or_admin(db, project_id=project_id, current_user=current_user)
    member = db.get(ProjectMember, member_id)
    if member is None or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found.")

    member.access_status = ProjectAccessStatusEnum.REJECTED
    member.reviewed_by = current_user.id
    member.reviewed_at = datetime.now(timezone.utc)
    member.review_note = payload.review_note

    db.commit()
    db.refresh(member)
    return _get_member_detail_or_404(db, member.id)


@router.post("/{project_id}/members", response_model=ProjectMemberDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager_user)])
def add_project_member(
    project_id: int,
    payload: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> ProjectMember:
    project = ensure_project_owner_or_admin(db, project_id=project_id, current_user=current_user)

    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    existing_member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.user_id,
        )
    )
    if existing_member is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has a project membership record.")

    member = ProjectMember(
        project_id=project_id,
        user_id=payload.user_id,
        member_role=payload.member_role,
        access_status=ProjectAccessStatusEnum.APPROVED,
        added_by=current_user.id,
        requested_at=datetime.now(timezone.utc),
        request_note=payload.request_note,
        reviewed_by=current_user.id,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _get_member_detail_or_404(db, member.id)


@router.patch("/{project_id}/members/{member_id}", response_model=ProjectMemberDetailRead, dependencies=[Depends(require_manager_user)])
def update_project_member(
    project_id: int,
    member_id: int,
    payload: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> ProjectMember:
    project = ensure_project_owner_or_admin(db, project_id=project_id, current_user=current_user)
    member = db.get(ProjectMember, member_id)
    if member is None or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found.")

    if member.user_id == project.owner_id and payload.member_role not in {None, ProjectMemberRoleEnum.OWNER}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project owner role cannot be changed from OWNER.",
        )

    data = payload.model_dump(exclude_unset=True)
    if "member_role" in data and data["member_role"] is not None:
        member.member_role = data["member_role"]
    if "review_note" in data:
        member.review_note = data["review_note"]
        member.reviewed_by = current_user.id
        member.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(member)
    return _get_member_detail_or_404(db, member.id)


@router.delete("/{project_id}/members/{member_id}", response_model=MessageSchema, dependencies=[Depends(require_manager_user)])
def remove_project_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> MessageSchema:
    project = ensure_project_owner_or_admin(db, project_id=project_id, current_user=current_user)
    member = db.get(ProjectMember, member_id)
    if member is None or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found.")

    if member.user_id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project owner cannot be removed from project members.",
        )

    db.delete(member)
    db.commit()
    return MessageSchema(message="Project member removed successfully.")