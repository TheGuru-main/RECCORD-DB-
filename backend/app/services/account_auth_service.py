"""RECCORD DB regular-user and organisation authentication service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gsp import GSPPlacement, gsp_place
from app.core.identity import require_phone_uid
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
    """Result of organisation signup, including its one-time credential."""

    organisation: Organisation
    access_token: str
    worker_credential: str


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
    phone: str,
    password: str,
) -> RegularSignupResult:
    """Create and authenticate a regular user account."""

    username = username.strip()
    name = name.strip()
    phone = phone.strip() if phone else None

    if not username:
        raise ValueError("username must not be empty")

    if not name:
        raise ValueError("name must not be empty")

    if not password:
        raise ValueError("password must not be empty")

    phone = require_phone_uid(phone, field="phone")

    existing_user = db.scalar(
        select(User).where(User.username == username).limit(1)
    )

    if existing_user is not None:
        raise ValueError("username is already registered")

    if phone:
        existing_phone = db.scalar(
            select(User.id).where(User.phone == phone).limit(1)
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
        account_uid=phone,
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
    """Authenticate a regular user independently of organisation accounts."""

    username = username.strip()

    user = db.scalar(
        select(User).where(
            User.username == username,
            User.account_type == "regular",
            User.status == "active",
            User.organisation_id.is_(None),
        )
    )

    if user is None or not verify_password(password, user.password_hash):
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
    """Create an organisation and issue its Worker Credential once."""

    business_name = business_name.strip()
    display_name = display_name.strip()
    country = country.strip()
    phone = phone.strip()
    language = language.strip()

    if not business_name:
        raise ValueError("business_name must not be empty")

    if not display_name:
        raise ValueError("display_name must not be empty")

    if not country:
        raise ValueError("country must not be empty")

    if not phone:
        raise ValueError("phone must not be empty")

    if not language:
        raise ValueError("language must not be empty")

    if not password:
        raise ValueError("password must not be empty")

    existing_organisation = db.scalar(
        select(Organisation).where(
            Organisation.phone == phone,
        ).limit(1)
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

    worker_credential = build_worker_credential_identity(
        organisation=organisation,
        worker_id=worker_id,
    )

    organisation.worker_id = worker_id
    organisation.worker_registration_credential_hash = hash_password(
        worker_credential
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
        worker_credential=worker_credential,
    )


def login_organisation(
    db: Session,
    *,
    phone: str,
    password: str,
) -> OrganisationLoginResult | None:
    """Authenticate an organisation account without reissuing its credential."""

    phone = phone.strip()

    organisation = db.scalar(
        select(Organisation).where(
            Organisation.phone == phone,
        )
    )

    if organisation is None:
        return None

    if not verify_password(password, organisation.password_hash):
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
