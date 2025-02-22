"""Add bidirectional communication support to property conversations

Revision ID: bidirectional_property_chat
Revises: 54b90b1a9f84
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "bidirectional_property_chat"
down_revision: Union[str, None] = "54b90b1a9f84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column(
        "property_conversations",
        sa.Column("role", sa.String(50), nullable=False, server_default="buyer"),
    )
    op.add_column(
        "property_conversations",
        sa.Column("conversation_status", sa.String(50), nullable=False, server_default="active"),
    )
    
    # Create a temporary column for the counterpart_id
    op.add_column(
        "property_conversations",
        sa.Column("counterpart_id", sa.String(255), nullable=True),
    )
    
    # Copy seller_id to counterpart_id for existing records
    op.execute(
        """
        UPDATE property_conversations
        SET counterpart_id = seller_id,
            role = 'buyer'
        """
    )
    
    # Make counterpart_id not nullable after data migration
    op.alter_column("property_conversations", "counterpart_id",
                    existing_type=sa.String(255),
                    nullable=False)
    
    # Create index for new columns
    op.create_index(
        op.f("ix_property_conversations_counterpart_id"),
        "property_conversations",
        ["counterpart_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_property_conversations_role"),
        "property_conversations",
        ["role"],
        unique=False,
    )
    
    # Drop the seller_id column and its index
    op.drop_index("ix_property_conversations_seller_id", table_name="property_conversations")
    op.drop_column("property_conversations", "seller_id")


def downgrade() -> None:
    # Add back the seller_id column
    op.add_column(
        "property_conversations",
        sa.Column("seller_id", sa.String(255), nullable=True),
    )
    
    # Copy counterpart_id back to seller_id for existing records
    op.execute(
        """
        UPDATE property_conversations
        SET seller_id = counterpart_id
        WHERE role = 'buyer'
        """
    )
    
    # Make seller_id not nullable after data migration
    op.alter_column("property_conversations", "seller_id",
                    existing_type=sa.String(255),
                    nullable=False)
    
    # Create index for seller_id
    op.create_index(
        op.f("ix_property_conversations_seller_id"),
        "property_conversations",
        ["seller_id"],
        unique=False,
    )
    
    # Drop the new columns and their indexes
    op.drop_index("ix_property_conversations_role", table_name="property_conversations")
    op.drop_index("ix_property_conversations_counterpart_id", table_name="property_conversations")
    op.drop_column("property_conversations", "counterpart_id")
    op.drop_column("property_conversations", "role")
    op.drop_column("property_conversations", "conversation_status") 