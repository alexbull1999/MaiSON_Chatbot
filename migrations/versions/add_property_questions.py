"""add property questions table

Revision ID: add_property_questions
Revises: # will be filled by alembic
Create Date: 2024-03-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_property_questions'
down_revision = None  # will be replaced with actual previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Create PropertyQuestion table
    op.create_table(
        'property_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.String(255), nullable=False),
        sa.Column('buyer_id', sa.String(255), nullable=False),
        sa.Column('seller_id', sa.String(255), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('question_message_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.Column('answer_text', sa.Text(), nullable=True),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['conversation_id'], ['property_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_message_id'], ['property_messages.id'], ondelete='CASCADE'),
        
        # Indexes
        sa.Index('ix_property_questions_id', 'id'),
        sa.Index('ix_property_questions_property_id', 'property_id'),
        sa.Index('ix_property_questions_buyer_id', 'buyer_id'),
        sa.Index('ix_property_questions_seller_id', 'seller_id'),
    )

def downgrade():
    # Drop the PropertyQuestion table
    op.drop_table('property_questions') 