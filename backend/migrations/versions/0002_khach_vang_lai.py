"""khach vang lai va ma truy cap don

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-03 10:00:00.000000

Đã được nhóm xác nhận ngày 03/11/2026 (BR-BUS-01, 07, 19):
- khach_hang.user_id cho phép NULL (khách vãng lai không có tài khoản).
- khach_hang.so_dien_thoai UNIQUE (nhận diện khách bằng số điện thoại).
- ve.ma_truy_cap_hash: SHA-256 (hex) của mã truy cập đơn, cùng giá trị cho
  mọi vé cùng ma_don; không lưu mã gốc.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('khach_hang', 'user_id', existing_type=sa.String(length=10), nullable=True)
    op.create_unique_constraint(op.f('uq_khach_hang_so_dien_thoai'), 'khach_hang', ['so_dien_thoai'])
    # NOT NULL không có default: chỉ chạy được khi bảng ve chưa có dữ liệu
    op.add_column('ve', sa.Column('ma_truy_cap_hash', sa.String(length=64), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    guest_count = op.get_bind().scalar(
        sa.text("SELECT count(*) FROM khach_hang WHERE user_id IS NULL")
    )
    # Không tự xóa dữ liệu: khách vãng lai có thể đã có vé
    if guest_count:
        raise RuntimeError(
            f"Còn {guest_count} khách vãng lai (khach_hang.user_id NULL), "
            "không thể khôi phục user_id NOT NULL. Xử lý dữ liệu này trước khi downgrade."
        )
    op.drop_column('ve', 'ma_truy_cap_hash')
    op.drop_constraint(op.f('uq_khach_hang_so_dien_thoai'), 'khach_hang', type_='unique')
    op.alter_column('khach_hang', 'user_id', existing_type=sa.String(length=10), nullable=False)
