"""RECCORD DB database schema initialization."""

from sqlalchemy import text

from app.core.database import Base, engine

from app.models.admin_update import AdminUpdate
from app.models.grid import Grid
from app.models.lookup import Lookup
from app.models.narration import Narration
from app.models.narration_version import NarrationVersion
from app.models.object import ObjectRecord
from app.models.object_version import ObjectVersion
from app.models.organisation import Organisation
from app.models.organisation_commit import OrganisationCommit
from app.models.organisation_version import OrganisationVersion
from app.models.regular_commit import RegularCommit
from app.models.regular_commit_version import RegularCommitVersion
from app.models.role import Role
from app.models.role_version import RoleVersion
from app.models.user import User
from app.models.user_version import UserVersion
from app.models.worker import Worker
from app.models.worker_version import WorkerVersion
from app.models.election import Election
from app.models.candidate import Candidate
from app.models.election_voter import ElectionVoter
from app.models.vote import Vote


def _add_column_if_missing(conn, table: str, column: str, ddl: str) -> None:
    exists = conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = :table AND column_name = :column
            """
        ),
        {"table": table, "column": column},
    ).first()
    if not exists:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def initialize_schema() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        try:
            _add_column_if_missing(conn, "election_voters", "country", "country VARCHAR(64)")
            _add_column_if_missing(conn, "election_voters", "state", "state VARCHAR(128)")
            _add_column_if_missing(conn, "election_voters", "lga", "lga VARCHAR(128)")
            _add_column_if_missing(conn, "candidates", "party", "party VARCHAR(255)")
            _add_column_if_missing(conn, "candidates", "about", "about TEXT")
            _add_column_if_missing(conn, "candidates", "details", "details TEXT")
            _add_column_if_missing(conn, "candidates", "country", "country VARCHAR(64)")
            _add_column_if_missing(conn, "candidates", "state", "state VARCHAR(128)")
            _add_column_if_missing(conn, "candidates", "lga", "lga VARCHAR(128)")
        except Exception:
            pass
