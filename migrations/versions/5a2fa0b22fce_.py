"""empty message

Revision ID: 5a2fa0b22fce
Revises: 4f91b682ac26
Create Date: 2018-07-11 13:57:03.269259

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a2fa0b22fce'
down_revision = '4f91b682ac26'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('steam_id', sa.String(length=40), nullable=False),
    sa.Column('steam_username', sa.String(length=80), nullable=False),
    sa.Column('created_at', sqlalchemy_utils.types.arrow.ArrowType(), nullable=False),
    sa.Column('updated_at', sqlalchemy_utils.types.arrow.ArrowType(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('steam_id')
    )
    op.add_column('rwr_accounts', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'rwr_accounts', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'rwr_accounts', type_='foreignkey')
    op.drop_column('rwr_accounts', 'user_id')
    op.drop_table('users')
    # ### end Alembic commands ###


def upgrade_rwr_account_stats():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_rwr_account_stats():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_servers_player_count():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_servers_player_count():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_steam_players_count():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_steam_players_count():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

