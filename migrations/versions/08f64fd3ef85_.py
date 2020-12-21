"""empty message

Revision ID: 08f64fd3ef85
Revises: b4382bcc33b4
Create Date: 2020-07-28 20:49:22.798716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08f64fd3ef85'
down_revision = 'b4382bcc33b4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_forbidden_to_access_api', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_forbidden_to_access_api')
    # ### end Alembic commands ###