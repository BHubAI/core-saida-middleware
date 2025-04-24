"""Abstract class for endpoints"""

from enum import Enum

import fastapi


class BaseEndpoint:
    """Base class for endpoints"""

    def __init__(self, tags: list[str | Enum], prefix: str):
        self.router = fastapi.APIRouter(tags=tags, prefix=prefix)

    def get_router(self) -> fastapi.APIRouter:
        """Get router instance"""
        return self.router
