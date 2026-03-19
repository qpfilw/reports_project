from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_db, get_current_active_user, get_db, require_manager_user
from app.models.enums import ProjectMemberRoleEnum
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.common import MessageSchema
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailRead,
    ProjectMemberCreate,
    ProjectMemberDetailRead,
    ProjectMemberRead,
    ProjectMemberUpdate,
    ProjectRead,
    ProjectUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_active_user)])

def _get_project_detail_or_404(db: Session, project_id: int) -> Project:
    stmt = (
        select(Project)
        .options(
            selectinload(Project.owner),
            selectinload(Project.members).selectinload(ProjectMember.user),
            selectinload(Project.members).selectinload(ProjectMember.creator),
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
        )
        .where(ProjectMember.id == member_id)
    )
    member = db.scalar(stmt)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found.")
    return member

@router.get("/", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    stmt = select(Project).order_by(Project.id)
    return list(db.scalars(stmt).all())

@router.get("/{project_id}", response_model=ProjectDetailRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    return _get_project_detail_or_404(db, project_id)

@router.post("/", response_model=ProjectDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager_user)])
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    owner = db.get(User, payload.owner_id)
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found.")

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
        added_by=payload.owner_id,
    )
    db.add(owner_member)

    db.commit()
    db.refresh(project)
    return _get_project_detail_or_404(db, project.id)

@router.patch("/{project_id}", response_model=ProjectDetailRead, dependencies=[Depends(require_manager_user)])
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

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
def list_project_members(project_id: int, db: Session = Depends(get_db)) -> list[ProjectMember]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    stmt = (
        select(ProjectMember)
        .options(
            selectinload(ProjectMember.user),
            selectinload(ProjectMember.creator),
        )
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.id)
    )
    return list(db.scalars(stmt).all())

@router.post("/{project_id}/members", response_model=ProjectMemberDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager_user)])
def add_project_member(
    project_id: int,
    payload: ProjectMemberCreate,
    db: Session = Depends(get_db),
) -> ProjectMember:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.added_by is not None:
        creator = db.get(User, payload.added_by)
        if creator is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator user not found.")

    existing_member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.user_id,
        )
    )
    if existing_member is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a project member.")

    member = ProjectMember(
        project_id=project_id,
        user_id=payload.user_id,
        member_role=payload.member_role,
        added_by=payload.added_by,
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
) -> ProjectMember:
    member = db.get(ProjectMember, member_id)
    if member is None or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found.")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)
    return _get_member_detail_or_404(db, member.id)

@router.delete("/{project_id}/members/{member_id}", response_model=MessageSchema, dependencies=[Depends(require_manager_user)])
def remove_project_member(project_id: int, member_id: int, db: Session = Depends(get_db)) -> MessageSchema:
    member = db.get(ProjectMember, member_id)
    if member is None or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found.")

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if member.user_id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project owner cannot be removed from project members.",
        )

    db.delete(member)
    db.commit()
    return MessageSchema(message="Project member removed successfully.")