from __future__ import annotations


class PlatformError(Exception):
    """Base exception for platform connector failures."""


class PlatformAuthError(PlatformError):
    """Authentication failed or session invalid."""


class PlatformOtpRequired(PlatformError):
    """OTP required to complete login."""


class PlatformBlockedError(PlatformError):
    """Bot protection / blocked / captcha encountered."""


class PlatformTimeoutError(PlatformError):
    """Timeout while calling platform."""


class PlatformSearchError(PlatformError):
    """Search failed for platform-specific reasons."""
