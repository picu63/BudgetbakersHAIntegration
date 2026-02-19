"""Data coordinator for BudgetBakers Wallet."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    BudgetBakersApiClient,
    BudgetBakersApiError,
    BudgetBakersAuthError,
    BudgetBakersRateLimitError,
)
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BudgetBakersDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates data updates from BudgetBakers Wallet API."""

    def __init__(self, hass: HomeAssistant, api_client: BudgetBakersApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="BudgetBakers Wallet",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._api_client = api_client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API and return normalized payload for entities."""
        try:
            result = await self._api_client.get_last_week_transactions_all_active_accounts()
            return {
                "transactions": result.transactions,
                "total_transactions": len(result.transactions),
                "account_count": result.account_count,
                "active_account_ids": result.active_account_ids,
                "requests_made": result.requests_made,
                "updated_at": datetime.now(UTC),
                "last_error": None,
            }
        except BudgetBakersAuthError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except BudgetBakersRateLimitError as err:
            if err.retry_after is not None and err.retry_after > 0:
                _LOGGER.warning(
                    "Rate limit exceeded. Waiting %s seconds before next retry.",
                    err.retry_after,
                )
                await asyncio.sleep(err.retry_after)
            raise UpdateFailed("Rate limit exceeded") from err
        except BudgetBakersApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
