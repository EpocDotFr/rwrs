"""empty message

Revision ID: f25d06f0afbd
Revises: 68f333014dfa
Create Date: 2023-09-07 17:51:40.314962

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f25d06f0afbd'
down_revision = '68f333014dfa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('hash_idx', table_name='rwr_account_stats')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('hash_idx', 'rwr_account_stats', ['hash'], unique=False)
    # ### end Alembic commands ###
