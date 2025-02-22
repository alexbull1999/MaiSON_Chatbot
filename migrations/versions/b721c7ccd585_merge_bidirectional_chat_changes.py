"""merge bidirectional chat changes

Revision ID: b721c7ccd585
Revises: 7385e6000442, bidirectional_property_chat
Create Date: 2025-02-22 12:30:20.101829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b721c7ccd585'
down_revision: Union[str, None] = ('7385e6000442', 'bidirectional_property_chat')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
