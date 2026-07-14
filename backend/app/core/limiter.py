"""Shared rate limiter.

Lives in its own module so route modules can import it without pulling in
app.main (which imports the routers — that would be a circular import).

Note: the default backend is in-memory, so limits are per-process. That is
correct for a single-container deployment; a multi-replica deployment should
point slowapi at Redis instead.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
