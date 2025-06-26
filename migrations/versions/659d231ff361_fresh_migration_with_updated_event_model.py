"""Fresh migration with updated Event model

Revision ID: 659d231ff361
Revises: 
Create Date: 2025-06-26 09:51:47.206038

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '659d231ff361'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('speaker_names', sa.JSON(), nullable=True),       # New
        sa.Column('category', sa.String(length=100), nullable=True), # New
        sa.Column('youtube_link', sa.String(length=255), nullable=True),  # New
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.userid']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('events')
