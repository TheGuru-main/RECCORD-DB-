"""RECCORD DB organisation role service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role


def list_roles(
    db: Session,
    *,
    organisation_id: str,
) -> list[Role]:
    return list(
        db.scalars(
            select(Role).where(
                Role.organisation_id == organisation_id,
                Role.active.is_(True),
            )
        )
    )


def create_role(
    db: Session,
    *,
    organisation_id: str,
    name: str,
) -> Role:
    name = name.strip()
    if not name:
        raise ValueError("role name must not be empty")

    existing = db.scalar(
        select(Role).where(
            Role.organisation_id == organisation_id,
            Role.name == name,
        )
    )
    if existing is not None:
        raise ValueError("role name already exists")

    role = Role(
        organisation_id=organisation_id,
        name=name,
        active=True,
    )
    db.add(role)
    db.flush()
    return role
