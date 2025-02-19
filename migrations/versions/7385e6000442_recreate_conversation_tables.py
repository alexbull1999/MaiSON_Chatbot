"""recreate_conversation_tables

Revision ID: 7385e6000442
Revises: 54b90b1a9f84
Create Date: 2025-02-19 16:48:26.297322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7385e6000442'
down_revision: Union[str, None] = '54b90b1a9f84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('external_references', sa.Column('general_conversation_id', sa.Integer(), nullable=True))
    op.add_column('external_references', sa.Column('property_conversation_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_external_references_general_conversation_id'), 'external_references', ['general_conversation_id'], unique=False)
    op.create_index(op.f('ix_external_references_property_conversation_id'), 'external_references', ['property_conversation_id'], unique=False)
    op.create_foreign_key(None, 'external_references', 'general_conversations', ['general_conversation_id'], ['id'])
    op.create_foreign_key(None, 'external_references', 'property_conversations', ['property_conversation_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'external_references', type_='foreignkey')
    op.drop_constraint(None, 'external_references', type_='foreignkey')
    op.drop_index(op.f('ix_external_references_property_conversation_id'), table_name='external_references')
    op.drop_index(op.f('ix_external_references_general_conversation_id'), table_name='external_references')
    op.drop_column('external_references', 'property_conversation_id')
    op.drop_column('external_references', 'general_conversation_id')
    # ### end Alembic commands ###
