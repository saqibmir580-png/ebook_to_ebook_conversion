"""Add file_path column to uploads table

Revision ID: add_file_path_001
Revises: 1e2d9efef6c5
Create Date: 2025-08-18 02:48:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_file_path_001'
down_revision = '1e2d9efef6c5'
branch_labels = None
depends_on = None


def upgrade():
    # Add the missing file_path column
    op.add_column('uploads', sa.Column('file_path', sa.String(), nullable=False, server_default=''))
    
    # Remove the server_default after adding the column
    op.alter_column('uploads', 'file_path', server_default=None)


def downgrade():
    # Remove the file_path column
    op.drop_column('uploads', 'file_path')
