"""Nguồn thời gian "hiện tại" duy nhất; test thay bằng dependency_overrides[get_now]."""

from datetime import UTC, date, datetime, timedelta, timezone

VIETNAM_TZ = timezone(timedelta(hours=7))


def get_now() -> datetime:
    return datetime.now(UTC)


def vietnam_date(moment: datetime) -> date:
    """Ngày theo giờ Việt Nam, khớp cách lưu chuyen_xe.ngay_khoi_hanh."""
    return moment.astimezone(VIETNAM_TZ).date()
