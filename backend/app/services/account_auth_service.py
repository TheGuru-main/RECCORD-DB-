"""RECCORD DB regular-user and organisation authentication service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gsp import GSPPlacement
from app.core.identity import require_phone_uid
from app.models.organisation import Organisation
from app.models.user import User
from app.services.auth_service import hash_password, verify_password
from app.services.placement_service import (
    place_organisation_signup,
    place_regular_user_signup,
)
from app.services.token_service import create_access_token
from app.services.worker_credential_service import (
    build_worker_credential_identity,
    generate_worker_id,
)


@dataclass(frozen=True)
class RegularSignupResult:
    user: User
    placement: GSPPlacement
    access_token: str


@dataclass(frozen=True)
class RegularLoginResult:
    user: User
    access_token: str


@dataclass(frozen=True)
class OrganisationSignupResult:
    organisation: Organisation
    access_token: str
    worker_credential: str
    placement: GSPPlacement


@dataclass(frozen=True)
class OrganisationLoginResult:
    organisation: Organisation
    access_token: str


def signup_regular_user(
    db: Session,
    *,
    name: str,
    phone: str,
    password: str,
    username: str | None = None,
    language: str | None = "en",
) -> RegularSignupResult:
    """Phone is identity uID. Signup placement uses fullname + phone only."""
    name = (name or "").strip()
    phone = require_phone_uid(phone, field="phone")
    username = phone

    if not name:
        raise ValueError("name must not be empty")
    if not password:
        raise ValueError("password must not be empty")

    if db.scalar(select(User.id).where(User.phone == phone).limit(1)):
        raise ValueError("phone number is already registered")
    if db.scalar(select(User.id).where(User.username == username).limit(1)):
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

    placement = place_regular_user_signup(
        phone_uid=phone,
        full_name=name,
        language=language or "en",
    )
    access_token = create_access_token(subject=str(user.id), account_type="regular")
    return RegularSignupResult(user=user, placement=placement, access_token=access_token)


def login_regular_user(
    db: Session,
    *,
    username: str | None = None,
    phone: str | None = None,
    password: str,
) -> RegularLoginResult | None:
    ident = (phone or username or "").strip()
    if not ident:
        return None
    try:
        phone_uid = require_phone_uid(ident, field="phone")
    except ValueError:
        phone_uid = None

    user = None
    if phone_uid:
        user = db.scalar(
            select(User).where(
                User.phone == phone_uid,
                User.account_type == "regular",
                User.status == "active",
                User.organisation_id.is_(None),
            )
        )
    if user is None:
        user = db.scalar(
            select(User).where(
                User.username == ident,
                User.account_type == "regular",
                User.status == "active",
                User.organisation_id.is_(None),
            )
        )
    if user is None or not verify_password(password, user.password_hash):
        return None

    access_token = create_access_token(subject=str(user.id), account_type="regular")
    return RegularLoginResult(user=user, access_token=access_token)


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
    business_name = business_name.strip()
    display_name = display_name.strip()
    country = country.strip()
    phone = require_phone_uid(phone, field="phone")
    language = (language or "en").strip() or "en"

    if not business_name:
        raise ValueError("business_name must not be empty")
    if not display_name:
        raise ValueError("display_name must not be empty")
    if not country:
        raise ValueError("country must not be empty")
    if not password:
        raise ValueError("password must not be empty")

    if db.scalar(select(Organisation).where(Organisation.phone == phone).limit(1)):
        raise ValueError("organisation phone number is already registered")

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
    organisation.worker_registration_credential_hash = hash_password(worker_credential)
    db.flush()

    # Org fixed face: org display name + org phone
    placement = place_organisation_signup(
        phone_uid=phone,
        org_display_name=display_name,
        language=language,
    )

    access_token = create_access_token(
        subject=str(organisation.id),
        account_type="organisation",
        organisation_id=str(organisation.id),
    )
    return OrganisationSignupResult(
        organisation=organisation,
        access_token=access_token,
        worker_credential=worker_credential,
        placement=placement,
    )


def login_organisation(
    db: Session,
    *,
    phone: str,
    password: str,
) -> OrganisationLoginResult | None:
    phone = require_phone_uid(phone, field="phone")
    organisation = db.scalar(select(Organisation).where(Organisation.phone == phone))
    if organisation is None:
        return None
    if not verify_password(password, organisation.password_hash):
        return None
    access_token = create_access_token(
        subject=str(organisation.id),
        account_type="organisation",
        organisation_id=str(organisation.id),
    )
    return OrganisationLoginResult(organisation=organisation, access_token=access_token)
