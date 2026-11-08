"""Giới hạn số lần đăng nhập sai theo (tên đăng nhập, IP), lưu trong bộ nhớ.

Giới hạn đã biết (ghi ở docs/API.md): bộ đếm nằm trong bộ nhớ của MỘT tiến trình,
không dùng chung giữa nhiều worker/máy chủ và mất khi khởi động lại.
"""

import math
from collections import deque
from datetime import datetime, timedelta

LoginKey = tuple[str, str]

# Quá số khóa này thì quét bỏ các khóa đã hết hạn, để bộ nhớ không phình khi
# bị thử hàng loạt tên đăng nhập ngẫu nhiên
SWEEP_THRESHOLD = 1024


def minutes_to_wait(wait: timedelta) -> int:
    """Số phút báo cho người dùng: làm tròn lên, tối thiểu 1."""
    return max(1, math.ceil(wait.total_seconds() / 60))


class LoginRateLimiter:
    """Cửa sổ trượt: quá `max_attempts` lần sai trong `window` thì bị khóa."""

    def __init__(self, max_attempts: int, window: timedelta) -> None:
        self.max_attempts = max_attempts
        self.window = window
        self._failures: dict[LoginKey, deque[datetime]] = {}

    def _recent(self, key: LoginKey, now: datetime) -> deque[datetime]:
        failures = self._failures.get(key)
        if failures is None:
            return deque()
        while failures and failures[0] + self.window <= now:
            failures.popleft()
        if not failures:
            del self._failures[key]
        return failures

    def retry_after(self, key: LoginKey, now: datetime) -> timedelta | None:
        """Thời gian còn phải chờ nếu đang bị khóa, None nếu được thử tiếp."""
        failures = self._recent(key, now)
        if len(failures) < self.max_attempts:
            return None
        # Lần sai cũ nhất trong số max_attempts lần gần nhất hết hạn thì được thử lại
        return failures[-self.max_attempts] + self.window - now

    def record_failure(self, key: LoginKey, now: datetime) -> None:
        if len(self._failures) >= SWEEP_THRESHOLD:
            for stale_key in list(self._failures):
                self._recent(stale_key, now)
        failures = self._recent(key, now)
        failures.append(now)
        self._failures[key] = failures

    def reset(self, key: LoginKey) -> None:
        self._failures.pop(key, None)
