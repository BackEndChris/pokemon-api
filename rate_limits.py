"""Thread-safe, bounded, in-process sliding-window request limits."""
from collections import deque
from hashlib import sha256
import math
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request
import config


class RateLimiter:
    def __init__(self, clock=monotonic, max_keys=10000):
        self.clock = clock
        self.max_keys = max_keys
        self.lock = Lock()
        self.buckets = {}

    def reset(self):
        with self.lock:
            self.buckets.clear()

    def check(self, rules):
        """Check all rules atomically; blocked requests do not prolong the ban."""
        now = self.clock()
        window = config.RATE_WINDOW_SECONDS
        with self.lock:
            for key, times in list(self.buckets.items()):
                while times and times[0] <= now - window:
                    times.popleft()
                if not times:
                    del self.buckets[key]
            retry = 0
            for key, limit in rules:
                times = self.buckets.get(key, ())
                if len(times) >= limit:
                    retry = max(retry, math.ceil(times[0] + window - now))
            new_keys = {key for key, _ in rules} - self.buckets.keys()
            if len(self.buckets) + len(new_keys) > self.max_keys:
                retry = max(retry, window)
            if retry:
                raise HTTPException(429, "Too many requests; try again later", headers={"Retry-After": str(max(1, retry))})
            for key, _ in rules:
                self.buckets.setdefault(key, deque()).append(now)


limiter = RateLimiter()


def source(request: Request):
    # Never trust X-Forwarded-For supplied directly by a client.
    return request.client.host if request.client else "unknown"


def registration_limit(request: Request):
    limiter.check([(("register", source(request)), config.REGISTER_LIMIT)])


def login_source_limit(request: Request):
    limiter.check([(("login-source", source(request)), config.LOGIN_SOURCE_LIMIT)])


def login_account_limit(request: Request, username: str):
    # Account + source, rather than global account lockouts that anyone could trigger.
    account = sha256(username.encode("utf-8")).hexdigest()
    limiter.check([(("login-account", source(request), account), config.LOGIN_ACCOUNT_LIMIT)])


def upload_limit(request: Request, user_id: int):
    limiter.check([
        (("upload-source", source(request)), config.UPLOAD_LIMIT),
        (("upload-user", user_id), config.UPLOAD_LIMIT),
    ])
