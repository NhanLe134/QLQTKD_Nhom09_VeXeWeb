"""khoa data api cua supabase

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-04 10:00:00.000000

Supabase cấp sẵn quyền trên schema public cho role anon và authenticated, nên
ai có anon key cũng đọc/ghi được bảng qua Data API. Migration này thu hồi mọi
quyền của hai role trên bảng và sequence trong public, kể cả quyền mặc định cho
bảng tạo sau (do role chạy migration tạo). Backend kết nối bằng role postgres
nên không bị ảnh hưởng. Không đổi cấu trúc bảng.

Trên PostgreSQL Docker không có hai role này thì bỏ qua.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DATA_API_ROLES = ("anon", "authenticated")


def for_each_existing_role(statements: list[str]) -> str:
    """Khối DO chạy các câu lệnh (có %I là tên role) cho role đang tồn tại."""
    roles = ", ".join(f"'{role}'" for role in DATA_API_ROLES)
    body = "\n".join(f"            EXECUTE format('{sql}', role_name);" for sql in statements)
    return f"""
    DO $$
    DECLARE
        role_name text;
    BEGIN
        FOREACH role_name IN ARRAY ARRAY[{roles}] LOOP
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
{body}
            END IF;
        END LOOP;
    END
    $$;
    """


def upgrade() -> None:
    """Thu hồi quyền của anon, authenticated trên bảng và sequence của public."""
    op.execute(for_each_existing_role([
        "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM %I",
        "REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM %I",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM %I",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM %I",
    ]))


def downgrade() -> None:
    """Trả lại quyền như mặc định của Supabase (mở lại Data API)."""
    op.execute(for_each_existing_role([
        "GRANT ALL ON ALL TABLES IN SCHEMA public TO %I",
        "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO %I",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO %I",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO %I",
    ]))
