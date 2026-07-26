"""Replaceable boundaries for external services."""

from backend.integrations.providers import (
    AzureEmailProvider,
    RecaptchaProvider,
    XProvider,
)

__all__ = ["AzureEmailProvider", "RecaptchaProvider", "XProvider"]
