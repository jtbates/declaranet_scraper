"""Initial models

Revision ID: 93e3ab35116d
Revises: 
Create Date: 2016-12-23 16:11:37.483313

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93e3ab35116d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dependencies',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('DEPENDENCY', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_index(op.f('ix_dependencies_DEPENDENCY'), 'dependencies', ['DEPENDENCY'], unique=True)
    op.create_table('servants',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('NAME', sa.String(), nullable=False),
    sa.Column('DECL0_DEP_ID', sa.Integer(), nullable=True),
    sa.Column('DECL0_TYPE', sa.Enum('I', 'M', 'C'), nullable=True),
    sa.Column('DECL0_SENT', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['DECL0_DEP_ID'], ['dependencies.ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_index('ix_decl0', 'servants', ['NAME', 'DECL0_DEP_ID', 'DECL0_TYPE', 'DECL0_SENT'], unique=True)
    op.create_table('declarations',
    sa.Column('ID', sa.Integer(), nullable=False),
    sa.Column('SERVANT_ID', sa.Integer(), nullable=True),
    sa.Column('DEPENDENCY_ID', sa.Integer(), nullable=True),
    sa.Column('TYPE', sa.Enum('I', 'M', 'C'), nullable=True),
    sa.Column('SENT', sa.Date(), nullable=True),
    sa.Column('PDF', sa.BLOB(), nullable=True),
    sa.Column('SHA256', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['DEPENDENCY_ID'], ['dependencies.ID'], ),
    sa.ForeignKeyConstraint(['SERVANT_ID'], ['servants.ID'], ),
    sa.PrimaryKeyConstraint('ID')
    )
    op.create_index(op.f('ix_declarations_SHA256'), 'declarations', ['SHA256'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_declarations_SHA256'), table_name='declarations')
    op.drop_table('declarations')
    op.drop_index('ix_decl0', table_name='servants')
    op.drop_table('servants')
    op.drop_index(op.f('ix_dependencies_DEPENDENCY'), table_name='dependencies')
    op.drop_table('dependencies')
    # ### end Alembic commands ###
