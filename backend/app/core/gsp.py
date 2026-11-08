"""
RECCORD DB — Guru Separation Protocol (Wizard grid).

Grid: 54 columns × 64 rows (rows 1..64).

Rules:
  - User signup: Startrow from user fullname + phone uID only (identity on their face).
  - Org signup: Startrow from org display name + org phone (org face fixed).
  - Worker: NO Startrow at register (messaging Startrow later only).
  - Object commit: object name + account phone uID; regular=user phone, org/worker=org phone.
  - Object uses replicas: k = 0..4 (5 positions), D = 8.
  - Language only sets alphabet length for column modulus.
  - Never SQL UUID for placement math.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.identity import require_phone_uid

AccountType = Literal["regular", "organisation"]

GRID_COLS = 54
GRID_ROWS = 64

# Locked GSP constants
RACK_JUMP = 8          # D
NUM_SPLITS = 5         # k = 0,1,2,3,4  (primary + replicas; not 6)

DEFAULT_ALPHABET = "abcdefghijklmnopqrstuvwxyz"


@dataclass(frozen=True)
class GSPPlacement:
    kind: str  # "user_signup" | "org_signup" | "object" | "vote"
    account_type: AccountType
    account_uid: str
    label: str
    L: int
    S: int
    c: int
    alphabet_len: int
    language: str
    start_row: int
    start_col: int
    key: str
    splits: tuple[tuple[int, int, int], ...]  # (k, row_k, col_k) length NUM_SPLITS
    cell_index: int


def normalize_label(name: str) -> str:
    normalized = "".join((name or "").split())
    if not normalized:
        raise ValueError("name must not be empty")
    return normalized


def sum_uid(phone_uid: str) -> int:
    phone = require_phone_uid(phone_uid, field="phone_uid")
    return sum(int(ch) for ch in phone if ch.isdigit())


def alphabet_for_language(language: str | None) -> str:
    lang = (language or "en").lower().split("-")[0]
    tables = {
        "en": DEFAULT_ALPHABET,
        "fr": DEFAULT_ALPHABET,
        "es": DEFAULT_ALPHABET,
        "pt": DEFAULT_ALPHABET,
        "de": DEFAULT_ALPHABET,
        "yo": "abdeẹefghiíjklmnoóọprsṣtuúwy",
        "ha": "abcdefghiƙjklmnoɓprstuwyzɗ",
        "ig": DEFAULT_ALPHABET,
    }
    return tables.get(lang, DEFAULT_ALPHABET)


def fold_char(ch: str) -> str:
    table = str.maketrans(
        "áàâäãåāéèêëēíìîïīóòôöõōúùûüūñçşṣẹọ"
        "ÁÀÂÄÃÅĀÉÈÊËĒÍÌÎÏĪÓÒÔÖÕŌÚÙÛÜŪÑÇŞṢẸỌ",
        "aaaaaaeeeeeeiiiiioooooouuuuunessẹọ"
        "aaaaaaeeeeeeiiiiioooooouuuuunessẹọ",
    )
    return ch.translate(table)


def first_letter_index(text: str, alphabet: str) -> int:
    alpha = alphabet.lower()
    for raw in text:
        if not raw.isalpha():
            continue
        ch = fold_char(raw).lower()
        if ch in alpha:
            return alpha.index(ch)
        if ch[:1] in alpha:
            return alpha.index(ch[0])
        if "a" <= ch[:1] <= "z":
            return DEFAULT_ALPHABET.index(ch[0]) % len(alpha)
    return 0


def compute_start_row(L: int, S: int) -> int:
    """start_row = ((L + S - 1) mod 64) + 1"""
    return ((L + S - 1) % GRID_ROWS) + 1


def split_cell(
    *,
    start_row_1: int,
    c: int,
    k: int,
    alphabet_len: int,
    D: int = RACK_JUMP,
) -> tuple[int, int]:
    """
    col_k = (c + k) mod alphabet_len  (kept in 0 .. GRID_COLS-1)
    row_k = ((start_row - 1 + k * D) mod 64) + 1
    D = 8, k in 0..4
    """
    mod = max(1, alphabet_len)
    col_k = (c + k) % mod
    col_k = col_k % GRID_COLS
    row_k = ((start_row_1 - 1 + k * D) % GRID_ROWS) + 1
    return row_k, col_k


def cell_index_0(row_1: int, col_0: int) -> int:
    return (row_1 - 1) * GRID_COLS + col_0


def _place(
    *,
    kind: str,
    account_type: AccountType,
    account_uid: str,
    label: str,
    language: str | None,
    with_replicas: bool,
) -> GSPPlacement:
    phone = require_phone_uid(account_uid, field="account_uid")
    label_norm = normalize_label(label)

    L = len(label_norm)
    S = sum_uid(phone)
    alphabet = alphabet_for_language(language)
    alphabet_len = len(alphabet)
    c = first_letter_index(label_norm, alphabet)
    srow = compute_start_row(L, S)

    if with_replicas:
        # Object / vote: k = 0..4 (5 positions), D = 8
        k_range = range(NUM_SPLITS)
    else:
        # Signup identity: Startrow only (primary cell), no replica scatter
        k_range = range(1)  # k = 0 only

    splits: list[tuple[int, int, int]] = []
    for k in k_range:
        row_k, col_k = split_cell(
            start_row_1=srow, c=c, k=k, alphabet_len=alphabet_len, D=RACK_JUMP
        )
        splits.append((k, row_k, col_k))

    primary_row, primary_col = splits[0][1], splits[0][2]
    key = f"{label_norm}:{phone}"

    return GSPPlacement(
        kind=kind,
        account_type=account_type,
        account_uid=phone,
        label=label_norm,
        L=L,
        S=S,
        c=c,
        alphabet_len=alphabet_len,
        language=(language or "en"),
        start_row=srow,
        start_col=primary_col,
        key=key,
        splits=tuple(splits),
        cell_index=cell_index_0(primary_row, primary_col),
    )


def place_user_signup(
    *,
    phone_uid: str,
    full_name: str,
    language: str | None = "en",
) -> GSPPlacement:
    """Regular user at signup: Startrow only, recognized by name + uID."""
    return _place(
        kind="user_signup",
        account_type="regular",
        account_uid=phone_uid,
        label=full_name,
        language=language,
        with_replicas=False,
    )


def place_org_signup(
    *,
    phone_uid: str,
    org_display_name: str,
    language: str | None = "en",
) -> GSPPlacement:
    """Organisation at signup: fixed org Startrow (name + org phone). No worker Startrow."""
    return _place(
        kind="org_signup",
        account_type="organisation",
        account_uid=phone_uid,
        label=org_display_name,
        language=language,
        with_replicas=False,
    )


def place_object(
    *,
    account_type: AccountType,
    account_phone_uid: str,
    object_name: str,
    language: str | None = "en",
) -> GSPPlacement:
    """
    Object commit with replicas (k=0..4, D=8).
    regular → user phone; organisation/worker → organisation phone.
    """
    return _place(
        kind="object",
        account_type=account_type,
        account_uid=account_phone_uid,
        label=object_name,
        language=language,
        with_replicas=True,
    )


def place_vote(
    *,
    voter_name: str,
    voter_phone: str,
    language: str | None = "en",
) -> GSPPlacement:
    """Vote placement: voter name + phone, with replicas."""
    return _place(
        kind="vote",
        account_type="regular",
        account_uid=voter_phone,
        label=voter_name,
        language=language,
        with_replicas=True,
    )
