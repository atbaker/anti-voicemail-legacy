"""carrier

Revision ID: 2946a4a70b4
Revises: 5256f3c602b
Create Date: 2015-10-10 22:35:01.056526

"""

# revision identifiers, used by Alembic.
revision = '2946a4a70b4'
down_revision = '5256f3c602b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mailbox', sa.Column('carrier', sa.String(length=50), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('mailbox', 'carrier')
    ### end Alembic commands ###
