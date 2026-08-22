"""RECCORD DB regular-user and organisation authentication service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gsp import GSPPlacement, gsp_place
from app.models.organisation import Organisation
from app.models.user import User
from app.services.auth_service import hash_password, verify_password
from app.services.token_service import create_access_token
from app.services.worker_credential_service import (
    build_worker_credential_identity,
    generate_worker_id,
)


@dataclass(frozen=True)
class RegularSignupResult:
    """Result of regular-user signup."""

    user: User
    placement: GSPPlacement
    access_token: str


@dataclass(frozen=True)
class RegularLoginResult:
    """Result of regular-user login."""

    user: User
    access_token: str


@dataclass(frozen=True)
class OrganisationSignupResult:
    """Result of organisation signup."""

    organisation: Organisation
    access_token: str


@dataclass(frozen=True)
class OrganisationLoginResult:
    """Result of organisation login."""

    organisation: Organisation
    access_token: str


def signup_regular_user(
    db: Session,
    *,
    username: str,
    name: str,
    phone: str | None,
    password: str,
) -> RegularSignupResult:
    """Create and authenticate a regular user account."""

    if not username.strip():
        raise ValueError("username must not be empty")

    if not name.strip():
        raise ValueError("name must not be empty")

    if not password:
        raise ValueError("password must not be empty")

    existing_user = db.scalar(
        select(User).where(
            User.username == username,
        )
    )

    if existing_user is not None:
        raise ValueError("username is already registered")

    if phone:
        existing_phone = db.scalar(
            select(User).where(
                User.phone == phone,
            )
        )

        if existing_phone is not None:
            raise ValueError("phone number is already registered")

    user = User(
        username=username,
        password_hash=hash_password(password),
        name=name,
        phone=phone,
        account_type="regular",
        organisation_id=None,
        status="active",
    )

    db.add(user)
    db.flush()

    placement = gsp_place(
        account_type="regular",
        account_id=str(user.id),
        name=name,
    )

    access_token = create_access_token(
        subject=str(user.id),
        account_type="regular",
    )

    return RegularSignupResult(
        user=user,
        placement=placement,
        access_token=access_token,
    )


def login_regular_user(
    db: Session,
    *,
    username: str,
    password: str,
) -> RegularLoginResult | None:
    """Authenticate a regular user."""

    user = db.scalar(
        select(User).where(
            User.username == username,
            User.account_type == "regular",
            User.status == "active",
            User.organisation_id.is_(None),
        )
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    access_token = create_access_token(
        subject=str(user.id),
        account_type="regular",
    )

    return RegularLoginResult(
        user=user,
        access_token=access_token,
    )


def signup_organisation(
    db: Session,
    *,
    business_name: str,
    display_name: str,
    country: str,
    phone: str,
    language: str,
    password: str,
) -> OrganisationSignupResult:
    """Create and authenticate an organisation account."""

    if not business_name.strip():
        raise ValueError("business_name must not be empty")

    if not display_name.strip():
        raise ValueError("display_name must not be empty")

    if not country.strip():
        raise ValueError("country must not be empty")

    if not phone.strip():
        raise ValueError("phone must not be empty")

    if not password:
        raise ValueError("password must not be empty")

    existing_organisation = db.scalar(
        select(Organisation).where(
            Organisation.phone == phone,
        )
    )

    if existing_organisation is not None:
        raise ValueError(
            "organisation phone number is already registered"
        )

    organisation = Organisation(
        business_name=business_name,
        display_name=display_name,
        country=country,
        phone=phone,
        language=language,
        password_hash=hash_password(password),
        worker_id="pending",
        worker_registration_credential_hash="pending",
    )

    db.add(organisation)
    db.flush()

    worker_id = generate_worker_id()

    credential_identity = build_worker_credential_identity(
        organisation=organisation,
        worker_id=worker_id,
    )

    organisation.worker_id = worker_id
    organisation.worker_registration_credential_hash = hash_password(
        credential_identity
    )

    db.flush()

    access_token = create_access_token(
        subject=str(organisation.id),
        account_type="organisation",
        organisation_id=str(organisation.id),
    )

    return OrganisationSignupResult(
        organisation=organisation,
        access_token=access_token,
    )


def login_organisation(
    db: Session,
    *,
    phone: str,
    password: str,
) -> OrganisationLoginResult | None:
    """Authenticate an organisation account."""

    organisation = db.scalar(
        select(Organisation).where(
            Organisation.phone == phone,
        )
    )

    if organisation is None:
        return None

    if not verify_password(
        password,
        organisation.password_hash,
    ):
        return None

    access_token = create_access_token(
        subject=str(organisation.id),
        account_type="organisation",
        organisation_id=str(organisation.id),
    )

    return OrganisationLoginResult(
        organisation=organisation,
        access_token=access_token,
    )
