from collections import defaultdict, deque
from datetime import datetime, timedelta, UTC


RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 10

_requests_store: dict[str, deque[datetime]] = defaultdict(deque)


def is_rate_limited(key: str) -> bool:
    now = datetime.now(UTC)
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)

    bucket = _requests_store[key]

    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        return True

    bucket.append(now)
    return False


def clear_rate_limits() -> None:
    _requests_store.clear()