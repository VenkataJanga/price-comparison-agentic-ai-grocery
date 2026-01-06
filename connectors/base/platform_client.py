from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from connectors.base.types import AuthState, PlatformHealth, UserContext
from core.schemas.grocery_item import GroceryItem
from core.schemas.platform_price import PlatformPrice


class PlatformClient(ABC):
    platform: str

    @abstractmethod
    def health(self) -> PlatformHealth:
        raise NotImplementedError

    @abstractmethod
    def ensure_authenticated(self, ctx: UserContext) -> AuthState:
        """
        If a reusable session exists, load it.
        If not, return NOT_AUTHENTICATED/OTP_REQUIRED as applicable.
        """
        raise NotImplementedError

    @abstractmethod
    def start_login(self, ctx: UserContext) -> AuthState:
        """
        Initiate login flow. Usually returns OTP_REQUIRED with auth_session_id.
        """
        raise NotImplementedError

    @abstractmethod
    def submit_otp(self, ctx: UserContext, auth_session_id: str, otp: str) -> AuthState:
        """
        Complete login using OTP and persist session.
        """
        raise NotImplementedError

    @abstractmethod
    def search(self, item: GroceryItem, ctx: UserContext) -> List[PlatformPrice]:
        """
        Search platform for item and return candidate price objects.
        """
        raise NotImplementedError
