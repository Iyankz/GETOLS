"""add snmp rw community and remove connection_type

Revision ID: 001_add_snmp_rw
Revises: 
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '001_add_snmp_rw'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('olts')]
    
    # Rename snmp_community_encrypted to snmp_ro_community_encrypted if exists
    if 'snmp_community_encrypted' in columns:
        op.alter_column('olts', 'snmp_community_encrypted', 
                        new_column_name='snmp_ro_community_encrypted')
    
    # Add snmp_rw_community_encrypted column if not exists
    if 'snmp_rw_community_encrypted' not in columns:
        op.add_column('olts', 
                      sa.Column('snmp_rw_community_encrypted', sa.Text(), nullable=True))
    
    # Remove connection_type column if exists (Telnet only now)
    if 'connection_type' in columns:
        op.drop_column('olts', 'connection_type')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('olts')]
    
    # Add back connection_type column if not exists
    if 'connection_type' not in columns:
        op.add_column('olts',
                      sa.Column('connection_type', sa.String(10), nullable=True, server_default='telnet'))
    
    # Remove snmp_rw_community_encrypted if exists
    if 'snmp_rw_community_encrypted' in columns:
        op.drop_column('olts', 'snmp_rw_community_encrypted')
    
    # Rename snmp_ro_community_encrypted back to snmp_community_encrypted if exists
    if 'snmp_ro_community_encrypted' in columns:
        op.alter_column('olts', 'snmp_ro_community_encrypted',
                        new_column_name='snmp_community_encrypted')
