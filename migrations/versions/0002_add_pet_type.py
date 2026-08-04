"""Add dog/cat pet type with a dog default for historical analyses."""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_pet_type"
down_revision = "0001_create_analyses"
branch_labels = None
depends_on = None

pet_type_enum = sa.Enum("dog", "cat", name="pet_type_enum")


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        pet_type_enum.create(bind, checkfirst=True)
    with op.batch_alter_table("analyses") as batch_op:
        batch_op.add_column(sa.Column("pet_type", pet_type_enum, nullable=False,
                                      server_default="dog"))
        batch_op.create_index("ix_analyses_pet_type_created_at", ["pet_type", "created_at"])


def downgrade():
    bind = op.get_bind()
    with op.batch_alter_table("analyses") as batch_op:
        batch_op.drop_index("ix_analyses_pet_type_created_at")
        batch_op.drop_column("pet_type")
    if bind.dialect.name == "postgresql":
        pet_type_enum.drop(bind, checkfirst=True)
