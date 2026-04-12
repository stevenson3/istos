"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # -- author --
    op.create_table(
        "author",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("period", sa.String(100)),
        sa.Column("description", sa.Text),
    )

    # -- book --
    op.create_table(
        "book",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("osis_id", sa.String(20), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("abbreviation", sa.String(10), nullable=False),
        sa.Column(
            "testament",
            sa.Enum("OT", "NT", name="testament_enum"),
            nullable=False,
        ),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("author.id")),
        sa.Column(
            "genre",
            sa.Enum(
                "Law", "History", "Wisdom", "Prophecy", "Poetry",
                "Gospel", "Acts", "Epistle", "Apocalyptic",
                name="genre_enum",
            ),
            nullable=False,
        ),
        sa.Column(
            "language_original",
            sa.Enum(
                "Hebrew", "Aramaic", "Greek", "HebrewAramaic",
                name="original_language_enum",
            ),
            nullable=False,
        ),
        sa.Column("order_num", sa.Integer, nullable=False),
    )

    # -- chapter --
    op.create_table(
        "chapter",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("book_id", sa.Integer, sa.ForeignKey("book.id"), nullable=False),
        sa.Column("number", sa.Integer, nullable=False),
        sa.UniqueConstraint("book_id", "number", name="uq_chapter_book_number"),
    )

    # -- verse --
    op.create_table(
        "verse",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chapter_id", sa.Integer, sa.ForeignKey("chapter.id"), nullable=False),
        sa.Column("book_id", sa.Integer, sa.ForeignKey("book.id"), nullable=False),
        sa.Column("number", sa.Integer, nullable=False),
        sa.Column("osis_ref", sa.String(50), unique=True, nullable=False),
    )
    op.create_index("idx_verse_osis_ref", "verse", ["osis_ref"])

    # -- verse_text --
    op.create_table(
        "verse_text",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("verse_id", sa.Integer, sa.ForeignKey("verse.id"), nullable=False),
        sa.Column(
            "language_code",
            sa.Enum("heb", "arc", "heb-virtual", "grc", "eng", name="language_code_enum"),
            nullable=False,
        ),
        sa.Column(
            "script_direction",
            sa.Enum("ltr", "rtl", name="script_direction_enum"),
            nullable=False,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("translation_name", sa.String(100), nullable=False),
        sa.Column("is_virtual", sa.Boolean, default=False, nullable=False),
        sa.Column("source_url", sa.String(500)),
        sa.Column("embedding_cross", Vector(768)),
        sa.Column("embedding_lang", Vector(768)),
    )
    op.create_index("idx_verse_text_verse_lang", "verse_text", ["verse_id", "language_code"])

    # HNSW indexes for vector similarity search (created after table)
    op.execute(
        "CREATE INDEX ON verse_text USING hnsw (embedding_cross vector_cosine_ops) "
        "WHERE embedding_cross IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX ON verse_text USING hnsw (embedding_lang vector_cosine_ops) "
        "WHERE embedding_lang IS NOT NULL"
    )

    # -- verse_token --
    op.create_table(
        "verse_token",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("verse_id", sa.Integer, sa.ForeignKey("verse.id"), nullable=False),
        sa.Column("language_code", sa.String(20), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("surface_form", sa.String(200), nullable=False),
        sa.Column("lemma", sa.String(200)),
        sa.Column("strong_number", sa.String(10)),
        sa.Column("morph_code", sa.String(50)),
        sa.Column("part_of_speech", sa.String(50)),
        sa.Column("gloss", sa.String(500)),
    )
    op.create_index("idx_verse_token_strong", "verse_token", ["strong_number"])

    # -- edge --
    op.create_table(
        "edge",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_verse_id", sa.Integer, sa.ForeignKey("verse.id"), nullable=False),
        sa.Column("target_verse_id", sa.Integer, sa.ForeignKey("verse.id"), nullable=False),
        sa.Column(
            "edge_type",
            sa.Enum(
                "CITATIONAL", "TOPICAL", "LINGUISTIC", "AUTHORIAL", "SEMANTIC",
                name="edge_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("weight", sa.Float, default=1.0, nullable=False),
        sa.Column("is_directed", sa.Boolean, default=False, nullable=False),
        sa.Column("metadata", sa.JSON),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_edge_source", "edge", ["source_verse_id", "edge_type"])
    op.create_index("idx_edge_target", "edge", ["target_verse_id", "edge_type"])

    # -- topic --
    op.create_table(
        "topic",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.Text),
    )

    # -- verse_topic --
    op.create_table(
        "verse_topic",
        sa.Column("verse_id", sa.Integer, sa.ForeignKey("verse.id"), primary_key=True),
        sa.Column("topic_id", sa.Integer, sa.ForeignKey("topic.id"), primary_key=True),
        sa.Column("weight", sa.Float, default=1.0, nullable=False),
        sa.UniqueConstraint("verse_id", "topic_id", name="uq_verse_topic"),
    )


def downgrade() -> None:
    op.drop_table("verse_topic")
    op.drop_table("topic")
    op.drop_table("edge")
    op.drop_table("verse_token")
    op.drop_table("verse_text")
    op.drop_table("verse")
    op.drop_table("chapter")
    op.drop_table("book")
    op.drop_table("author")

    op.execute("DROP TYPE IF EXISTS edge_type_enum")
    op.execute("DROP TYPE IF EXISTS language_code_enum")
    op.execute("DROP TYPE IF EXISTS script_direction_enum")
    op.execute("DROP TYPE IF EXISTS original_language_enum")
    op.execute("DROP TYPE IF EXISTS genre_enum")
    op.execute("DROP TYPE IF EXISTS testament_enum")
