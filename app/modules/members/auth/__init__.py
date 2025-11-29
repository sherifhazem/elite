"""Authentication package helpers.

This module intentionally avoids importing the routes blueprint at import time
to prevent circular imports when access-control utilities lazily import member
services. Import the blueprint directly from ``app.modules.members.auth.routes``
when needed.
"""

__all__ = []
