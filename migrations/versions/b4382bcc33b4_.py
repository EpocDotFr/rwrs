"""empty message

Revision ID: b4382bcc33b4
Revises: 950f85a369b7
Create Date: 2019-05-10 10:04:11.866957

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = 'b4382bcc33b4'
down_revision = '950f85a369b7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_friends',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('username', sa.String(length=16), nullable=False),
    sa.Column('created_at', sqlalchemy_utils.types.arrow.ArrowType(), nullable=False),
    sa.ForeignKeyConstraint(('user_id',), ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('user_id_idx', 'user_friends', ['user_id'], unique=False)
    op.create_index('user_id_username_idx', 'user_friends', ['user_id', 'username'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('user_id_username_idx', table_name='user_friends')
    op.drop_index('user_id_idx', table_name='user_friends')
    op.drop_table('user_friends')
    # ### end Alembic commands ###
