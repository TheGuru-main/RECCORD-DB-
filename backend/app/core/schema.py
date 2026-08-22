"""RECCORD DB database schema initialization."""

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


def initialize_schema() -> None:
    """Create all missing RECCORD DB tables in the configured database."""

    Base.metadata.create_all(bind=engine)
