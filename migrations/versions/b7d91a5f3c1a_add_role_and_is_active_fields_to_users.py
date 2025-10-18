"""Add role and is_active fields to users

Revision ID: b7d91a5f3c1a
Revises: 0a3b21a1b397
Create Date: 2025-10-18 17:05:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import expression

# revision identifiers, used by Alembic.
revision = "b7d91a5f3c1a"
down_revision = "0a3b21a1b397"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the role and permission schema changes."""

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_permissions_name"),
    )

    op.create_table(
        "user_permissions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "permission_id"),
    )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                sa.String(length=50),
                nullable=False,
                server_default="member",
            )
        )
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=expression.true(),
            )
        )
        batch_op.add_column(
            sa.Column("company_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_users_company_id_companies",
            "companies",
            ["company_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        "UPDATE users SET role = 'admin' WHERE role = 'member' AND COALESCE(is_admin, false) = true"
    )
    op.execute(
        "UPDATE users SET role = 'superadmin' WHERE COALESCE(is_admin, false) = true AND username = 'superadmin'"
    )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("role", server_default=None)
        batch_op.alter_column("is_active", server_default=None)
        batch_op.drop_column("is_admin")


def downgrade() -> None:
    """Revert the role and permission schema changes."""

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_admin",
                sa.Boolean(),
                nullable=False,
                server_default=expression.false(),
            )
        )

    op.execute(
        "UPDATE users SET is_admin = true WHERE role IN ('admin', 'superadmin')"
    )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("fk_users_company_id_companies", type_="foreignkey")
        batch_op.drop_column("company_id")
        batch_op.drop_column("is_active")
        batch_op.drop_column("role")
        batch_op.alter_column("is_admin", server_default=None)

    op.drop_table("user_permissions")
    op.drop_table("permissions")
