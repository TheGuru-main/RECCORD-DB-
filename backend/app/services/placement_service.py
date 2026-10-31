"""RECCORD DB placement service."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.gsp import GSPPlacement, gsp_place, normalize_name
from app.core.identity import require_phone_uid


@dataclass(frozen=True)
class VotePlacement:
    """Placement result for an E-Voting vote (primary + 5 replicas)."""

    primary_key: str
    replicas: list[str]          # exactly 5 replica keys
    voter_name: str
    voter_phone: str


def place_regular_commit(
    *,
    account_uid: str,
    object_name: str,
) -> GSPPlacement:
    """Calculate placement using the regular account's established uID."""
    return gsp_place(
        account_type="regular",
        account_uid=account_uid,
        name=object_name,
    )


def place_organisation_commit(
    *,
    account_uid: str,
    object_name: str,
) -> GSPPlacement:
    """Calculate placement using the organisation's established uID."""
    return gsp_place(
        account_type="organisation",
        account_uid=account_uid,
        name=object_name,
    )


def place_vote(
    *,
    voter_name: str,
    voter_phone: str,
) -> VotePlacement:
    """
    Place a vote using voter Name + uID.

    Creates 1 primary key + 5 replica keys.
    All keys are deterministic from the voter identity.
    """
    phone = require_phone_uid(voter_phone, field="voter_phone")
    name = normalize_name(voter_name)

    primary_key = f"vote:{name}:{phone}"

    # 5 deterministic replicas
    replicas = [
        f"vote:{name}:{phone}:r1",
        f"vote:{name}:{phone}:r2",
        f"vote:{name}:{phone}:r3",
        f"vote:{name}:{phone}:r4",
        f"vote:{name}:{phone}:r5",
    ]

    return VotePlacement(
        primary_key=primary_key,
        replicas=replicas,
        voter_name=voter_name.strip(),
        voter_phone=phone,
    )
