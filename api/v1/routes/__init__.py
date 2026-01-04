"""Routes package"""

from api.v1.routes import auth, threats, ai, analytics, streams, alerts

__all__ = ["auth", "threats", "ai", "analytics", "streams", "alerts"]
