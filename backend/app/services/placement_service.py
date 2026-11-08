"""Placement service — signup vs object vs vote (not mixed)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.gsp import GSPPlacement, place_object, place_user_signup, place_vote


def place_regular_user_signup(
    *,
    phone_uid: str,
    full_name: str,
    language: str | None = "en",
) -> GSPPlacement:
    return place_user_signup(
        account_type="regular",
        phone_uid=phone_uid,
        full_name=full_name,
        language=language,
    )


def place_organisation_signup(
    *,
    phone_uid: str,
    org_display_name: str,
    language: str | None = "en",
) -> GSPPlacement:
    """Org fixed face from org name + org phone at signup."""
    return place_user_signup(
        account_type="organisation",
        phone_uid=phone_uid,
        full_name=org_display_name,
        language=language,
    )


def place_regular_object(
    *,
    user_phone_uid: str,
    object_name: str,
    language: str | None = "en",
) -> GSPPlacement:
    return place_object(
        account_type="regular",
        account_phone_uid=user_phone_uid,
        object_name=object_name,
        language=language,
    )


def place_organisation_object(
    *,
    organisation_phone_uid: str,
    object_name: str,
    language: str | None = "en",
) -> GSPPlacement:
    """Worker and org admin both place on org grid (org phone uID)."""
    return place_object(
        account_type="organisation",
        account_phone_uid=organisation_phone_uid,
        object_name=object_name,
        language=language,
    )


@dataclass(frozen=True)
class VotePlacement:
    primary_key: str
    replicas: list[str]
    voter_name: str
    voter_phone: str
    start_row: int
    start_col: int
    cell_index: int
    splits: list[dict]


def place_vote_commit(
    *,
    voter_name: str,
    voter_phone: str,
    language: str | None = "en",
) -> VotePlacement:
    g = place_vote(
        voter_name=voter_name,
        voter_phone=voter_phone,
        language=language,
    )
    return VotePlacement(
        primary_key=g.key,
        replicas=[f"{g.key}:r{k}" for k in range(1, 6)],
        voter_name=voter_name.strip(),
        voter_phone=g.account_uid,
        start_row=g.start_row,
        start_col=g.start_col,
        cell_index=g.cell_index,
        splits=[{"k": k, "row": row, "col": col} for k, row, col in g.splits],
    )
