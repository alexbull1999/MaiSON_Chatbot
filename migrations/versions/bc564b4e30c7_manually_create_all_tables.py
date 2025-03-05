"""manually_create_all_tables

Revision ID: bc564b4e30c7
Revises: c4c526557e1f
Create Date: 2025-03-05 18:05:33.933844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bc564b4e30c7'
down_revision: Union[str, None] = 'c4c526557e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create general_conversations table
    op.create_table(
        'general_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('is_logged_in', sa.Boolean(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_general_conversations_id'), 'general_conversations', ['id'], unique=False)
    op.create_index(op.f('ix_general_conversations_session_id'), 'general_conversations', ['session_id'], unique=True)
    op.create_index(op.f('ix_general_conversations_user_id'), 'general_conversations', ['user_id'], unique=False)

    # Create general_messages table
    op.create_table(
        'general_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('intent', sa.String(length=50), nullable=True),
        sa.Column('message_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['general_conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_general_messages_conversation_id'), 'general_messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_general_messages_id'), 'general_messages', ['id'], unique=False)
    op.create_index(op.f('ix_general_messages_timestamp'), 'general_messages', ['timestamp'], unique=False)

    # Create property_conversations table
    op.create_table(
        'property_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('property_id', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('counterpart_id', sa.String(length=255), nullable=False),
        sa.Column('conversation_status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('property_context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_property_conversations_id'), 'property_conversations', ['id'], unique=False)
    op.create_index(op.f('ix_property_conversations_session_id'), 'property_conversations', ['session_id'], unique=True)
    op.create_index(op.f('ix_property_conversations_user_id'), 'property_conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_property_conversations_property_id'), 'property_conversations', ['property_id'], unique=False)
    op.create_index(op.f('ix_property_conversations_role'), 'property_conversations', ['role'], unique=False)
    op.create_index(op.f('ix_property_conversations_counterpart_id'), 'property_conversations', ['counterpart_id'], unique=False)

    # Create property_messages table
    op.create_table(
        'property_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('intent', sa.String(length=50), nullable=True),
        sa.Column('message_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['property_conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_property_messages_conversation_id'), 'property_messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_property_messages_id'), 'property_messages', ['id'], unique=False)
    op.create_index(op.f('ix_property_messages_timestamp'), 'property_messages', ['timestamp'], unique=False)

    # Create external_references table
    op.create_table(
        'external_references',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('general_conversation_id', sa.Integer(), nullable=True),
        sa.Column('property_conversation_id', sa.Integer(), nullable=True),
        sa.Column('service_name', sa.String(length=100), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('reference_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_synced', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['general_conversation_id'], ['general_conversations.id'], ),
        sa.ForeignKeyConstraint(['property_conversation_id'], ['property_conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_external_references_general_conversation_id'), 'external_references', ['general_conversation_id'], unique=False)
    op.create_index(op.f('ix_external_references_id'), 'external_references', ['id'], unique=False)
    op.create_index(op.f('ix_external_references_property_conversation_id'), 'external_references', ['property_conversation_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('external_references')
    op.drop_table('property_messages')
    op.drop_table('property_conversations')
    op.drop_table('general_messages')
    op.drop_table('general_conversations')
