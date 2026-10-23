"""Resolve authenticated RECCORD DB accounts from signed bearer tokens."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose.exceptions import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.organisation import Organisation
from app.models.user import User
from app.models.worker import Worker
from app.services.token_service import decode_access_token


_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Database-backed identity for an authenticated request."""

    account_type: str
    account_id: uuid.UUID
    user: User | None = None
    organisation: Organisation | None = None
    worker: Worker | None = None

    @property
    def organisation_id(self) -> uuid.UUID | None:
        """Return the organisation associated with this principal."""
        if self.organisation is not None:
            return self.organisation.id

        if self.user is not None:
            return self.user.organisation_id

        return None


def _unauthorized() -> HTTPException:
    """Build a consistent authentication failure response."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _parse_uuid(value: object) -> uuid.UUID:
    """Parse a UUID claim without trusting arbitrary token data."""
    if not isinstance(value, str):
        raise ValueError("UUID claim must be a string")

    return uuid.UUID(value)


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        _bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> AuthenticatedPrincipal:
    """Validate a bearer token and resolve its active database identity."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        claims = decode_access_token(credentials.credentials)

        subject_id = _parse_uuid(claims.get("sub"))
        account_type = claims.get("account_type")

        if account_type == "regular":
            user = db.get(User, subject_id)

            if (
                user is None
                or user.account_type != "regular"
                or user.status != "active"
                or user.organisation_id is not None
            ):
                raise _unauthorized()

            return AuthenticatedPrincipal(
                account_type="regular",
                account_id=user.id,
                user=user,
            )

        if account_type == "organisation":
            organisation_id = _parse_uuid(
                claims.get("organisation_id")
            )

            if organisation_id != subject_id:
                raise _unauthorized()

            organisation = db.get(Organisation, organisation_id)

            if organisation is None:
                raise _unauthorized()

            return AuthenticatedPrincipal(
                account_type="organisation",
                account_id=organisation.id,
                organisation=organisation,
            )

        if account_type == "worker":
            organisation_id = _parse_uuid(
                claims.get("organisation_id")
            )

            user = db.get(User, subject_id)

            if (
                user is None
                or user.account_type != "worker"
                or user.status != "active"
                or user.organisation_id != organisation_id
            ):
                raise _unauthorized()

            worker = (
                db.query(Worker)
                .filter(
                    Worker.user_id == user.id,
                    Worker.organisation_id == organisation_id,
                    Worker.status == "active",
                )
                .first()
            )

            if worker is None:
                raise _unauthorized()

            organisation = db.get(Organisation, organisation_id)

            if organisation is None:
                raise _unauthorized()

            return AuthenticatedPrincipal(
                account_type="worker",
                account_id=user.id,
                user=user,
                organisation=organisation,
                worker=worker,
            )

        raise _unauthorized()

    except HTTPException:
        raise
    except (JWTError, ValueError, TypeError, AttributeError):
        raise _unauthorized() from None
