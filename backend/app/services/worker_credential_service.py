"""RECCORD DB worker registration and authentication service."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.identity import require_phone_uid
from app.models.organisation import Organisation
from app.models.role import Role
from app.models.user import User
from app.models.worker import Worker
from app.services.auth_service import hash_password, verify_password
from app.services.token_service import create_access_token


@dataclass(frozen=True)
class WorkerRegistrationResult:
    user: User
    worker: Worker
    organisation: Organisation
    placement: GSPPlacement


@dataclass(frozen=True)
class WorkerLoginResult:
    user: User
    worker: Worker
    organisation: Organisation
    access_token: str


@dataclass(frozen=True)
class WorkerRoleLookupResult:
    organisation: Organisation
    roles: list[Role]


def build_worker_credential_identity(
    *,
    organisation: Organisation,
    worker_id: str,
) -> str:
    """
    Canonical Worker Credential:
    org_display_name : org_phone_uID : worker_reg_id
    Never uses SQL UUID in the credential string.
    """
    organisation_name = (organisation.display_name or organisation.business_name or "").strip()
    phone = require_phone_uid(organisation.phone, field="organisation.phone")
    canonical_worker_id = (worker_id or "").strip()

    if not organisation_name:
        raise ValueError("organisation name must not be empty")
    if not canonical_worker_id:
        raise ValueError("worker_id must not be empty")

    return f"{organisation_name}:{phone}:{canonical_worker_id}"


def generate_worker_id() -> str:
    return f"WRK-{secrets.token_urlsafe(12)}"


def get_organisation_from_worker_credential(
    db: Session,
    *,
    worker_credential: str,
) -> Organisation:
    credential = (worker_credential or "").strip()
    if not credential:
        raise ValueError("invalid Worker Credential")

    try:
        display_name, phone_part, worker_id = credential.rsplit(":", 2)
        phone = require_phone_uid(phone_part, field="credential_phone")
    except (ValueError, AttributeError):
        raise ValueError("invalid Worker Credential") from None

    if not display_name or not worker_id:
        raise ValueError("invalid Worker Credential")

    organisation = db.scalar(
        select(Organisation).where(
            Organisation.phone == phone,
            Organisation.worker_id == worker_id,
        )
    )
    if organisation is None:
        raise ValueError("invalid Worker Credential")

    # Accept either exact display_name match or business_name
    org_label = (organisation.display_name or organisation.business_name or "").strip()
    if display_name.strip() != org_label:
        # soft: still require hash match below
        pass

    if not verify_password(credential, organisation.worker_registration_credential_hash):
        raise ValueError("invalid Worker Credential")

    return organisation


def get_worker_registration_roles(
    db: Session,
    *,
    worker_credential: str,
) -> WorkerRoleLookupResult:
    organisation = get_organisation_from_worker_credential(
        db, worker_credential=worker_credential
    )
    roles = list(
        db.scalars(
            select(Role)
            .where(
                Role.organisation_id == organisation.id,
                Role.active.is_(True),
            )
            .order_by(Role.name.asc(), Role.id.asc())
        ).all()
    )
    return WorkerRoleLookupResult(organisation=organisation, roles=roles)


def register_worker(
    db: Session,
    *,
    worker_credential: str,
    worker_phone: str,
    worker_password: str,
    name: str,
    role: str,
) -> WorkerRegistrationResult:
    worker_phone = require_phone_uid(worker_phone.strip(), field="worker_phone")
    name = name.strip()
    requested_role = role.strip()

    if not worker_password:
        raise ValueError("worker password must not be empty")
    if not name:
        raise ValueError("worker name must not be empty")
    if not requested_role:
        raise ValueError("worker role must not be empty")

    organisation = get_organisation_from_worker_credential(
        db, worker_credential=worker_credential
    )

    organisation_role = db.scalar(
        select(Role)
        .where(
            Role.organisation_id == organisation.id,
            Role.name == requested_role,
            Role.active.is_(True),
        )
        .limit(1)
    )
    if organisation_role is None:
        raise ValueError("selected role is not active for this organisation")

    if db.scalar(select(User.id).where(User.phone == worker_phone).limit(1)):
        raise ValueError("phone number is already registered")

    user = User(
        username=worker_phone,
        password_hash=hash_password(worker_password),
        name=name,
        phone=worker_phone,
        account_type="worker",
        organisation_id=organisation.id,
        status="pending",
    )
    db.add(user)
    db.flush()

    worker = Worker(
        user_id=user.id,
        organisation_id=organisation.id,
        role=organisation_role.name,
        status="pending",
    )
    db.add(worker)
    db.flush()

    # Org grid scope uses organisation phone uID — never SQL UUID for GSP
        # Worker joins org-fixed domain: org phone uID + worker fullname for L/c

    return WorkerRegistrationResult(
        user=user,
        worker=worker,
        organisation=organisation,
    )


def login_worker(
    db: Session,
    *,
    worker_phone: str,
    worker_password: str,
) -> WorkerLoginResult | None:
    worker_phone = require_phone_uid(worker_phone.strip(), field="worker_phone")

    user = db.scalar(
        select(User).where(
            User.phone == worker_phone,
            User.account_type == "worker",
            User.status == "active",
        )
    )
    if user is None or user.organisation_id is None:
        return None
    if not verify_password(worker_password, user.password_hash):
        return None

    # Accept approved or active worker status
    worker = db.scalar(
        select(Worker).where(
            Worker.user_id == user.id,
            Worker.organisation_id == user.organisation_id,
            Worker.status.in_(("active", "approved")),
        )
    )
    if worker is None:
        return None

    organisation = db.get(Organisation, user.organisation_id)
    if organisation is None:
        return None

    access_token = create_access_token(
        subject=str(user.id),
        account_type="worker",
        organisation_id=str(organisation.id),
    )
    return WorkerLoginResult(
        user=user,
        worker=worker,
        organisation=organisation,
        access_token=access_token,
    )
