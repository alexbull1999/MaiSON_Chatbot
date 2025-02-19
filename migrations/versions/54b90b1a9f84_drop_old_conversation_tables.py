"""Drop old conversation tables

Revision ID: 54b90b1a9f84
Revises: 542695f1b434
Create Date: 2025-02-19 16:30:35.294871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '54b90b1a9f84'
down_revision: Union[str, None] = '542695f1b434'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # First, drop the external references foreign key
    op.drop_constraint('external_references_conversation_id_fkey', 'external_references', type_='foreignkey')
    op.drop_index('ix_external_references_conversation_id', table_name='external_references')
    
    # Then drop the messages table and its indexes
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_index('ix_messages_id', table_name='messages')
    op.drop_table('messages')
    
    # Now we can safely drop the conversations table and its indexes
    op.drop_index('ix_conversations_id', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    op.drop_table('conversations')
    
    # Drop the conversation_id column from external_references
    op.drop_column('external_references', 'conversation_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Add conversation_id column back to external_references
    op.add_column('external_references', sa.Column('conversation_id', sa.INTEGER(), autoincrement=False, nullable=True))
    
    # Recreate the conversations table
    op.create_table('conversations',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('user_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('user_email', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('property_id', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('seller_id', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('started_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('last_message_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='conversations_pkey')
    )
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'], unique=False)
    op.create_index('ix_conversations_id', 'conversations', ['id'], unique=False)
    
    # Recreate the messages table
    op.create_table('messages',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('role', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
        sa.Column('content', sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('intent', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
        sa.Column('message_metadata', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name='messages_conversation_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='messages_pkey')
    )
    op.create_index('ix_messages_id', 'messages', ['id'], unique=False)
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'], unique=False)
    
    # Restore external references constraint
    op.create_index('ix_external_references_conversation_id', 'external_references', ['conversation_id'], unique=False)
    op.create_foreign_key('external_references_conversation_id_fkey', 'external_references', 'conversations', ['conversation_id'], ['id'])
    # ### end Alembic commands ###
