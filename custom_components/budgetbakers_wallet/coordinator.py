"""Data coordinator for BudgetBakers Wallet."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
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
            now_utc = datetime.now(UTC)
            seven_days_ago = now_utc - timedelta(days=7)

            result = await self._api_client.get_transactions_all_active_accounts(days=30)
            transactions_last_7_days = [
                item
                for item in result.transactions
                if _is_record_on_or_after(item, seven_days_ago)
            ]

            return {
                "transactions": transactions_last_7_days,
                "total_transactions": len(transactions_last_7_days),
                "transaction_sum_30_days": _calculate_transaction_sum_30_days(result.transactions),
                "account_count": result.account_count,
                "active_account_ids": result.active_account_ids,
                "requests_made": result.requests_made,
                "updated_at": now_utc,
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


def _is_record_on_or_after(record: dict[str, Any], threshold: datetime) -> bool:
    """Return True if recordDate is on or after threshold."""
    record_date = record.get("recordDate")
    if not isinstance(record_date, str):
        return False

    try:
        parsed_date = datetime.fromisoformat(record_date.replace("Z", "+00:00"))
    except ValueError:
        return False

    return parsed_date >= threshold


def _calculate_transaction_sum_30_days(transactions: list[dict[str, Any]]) -> float:
    """Calculate sum of absolute transaction values in PLN for last 30 days."""
    total = 0.0
    for transaction in transactions:
        base_amount = transaction.get("baseAmount") or {}
        if base_amount.get("currencyCode") != "PLN":
            continue

        value = base_amount.get("value")
        if not isinstance(value, (int, float)):
            continue

        total += abs(float(value))

    return round(total, 2)
