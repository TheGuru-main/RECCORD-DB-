"""Placement service — signup Startrow vs object replicas (workers: no signup Startrow)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.gsp import (
    GSPPlacement,
    place_object,
    place_org_signup,
    place_user_signup,
    place_vote,
)


def place_regular_user_signup(
    *,
    phone_uid: str,
    full_name: str,
    language: str | None = "en",
) -> GSPPlacement:
    return place_user_signup(
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
    return place_org_signup(
        phone_uid=phone_uid,
        org_display_name=org_display_name,
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
    """Org admin and workers: always organisation phone uID."""
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
    # k=1..4 are replica keys (k=0 is primary)
    replicas = [f"{g.key}:r{k}" for k in range(1, len(g.splits))]
    return VotePlacement(
        primary_key=g.key,
        replicas=replicas,
        voter_name=voter_name.strip(),
        voter_phone=g.account_uid,
        start_row=g.start_row,
        start_col=g.start_col,
        cell_index=g.cell_index,
        splits=[{"k": k, "row": row, "col": col} for k, row, col in g.splits],
    )
