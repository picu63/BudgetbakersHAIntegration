"""Sensor platform for BudgetBakers Wallet."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACCOUNT_COUNT,
    ATTR_ACTIVE_ACCOUNT_IDS,
    ATTR_LAST_ERROR,
    ATTR_REQUESTS_MADE,
    ATTR_TOTAL_TRANSACTIONS,
    ATTR_TRANSACTIONS,
    ATTR_UPDATED_AT,
    DEFAULT_NAME,
    DOMAIN,
    MAX_TRANSACTIONS_IN_ATTRIBUTES,
)
from .coordinator import BudgetBakersDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BudgetBakers Wallet sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BudgetBakersTransactionsSensor(coordinator, entry)])


class BudgetBakersTransactionsSensor(
    CoordinatorEntity[BudgetBakersDataUpdateCoordinator], SensorEntity
):
    """Represents a sensor with all transactions from the last 7 days."""

    _attr_has_entity_name = True
    _attr_name = "Transactions (last 7 days)"
    _attr_icon = "mdi:bank-transfer"

    def __init__(
        self,
        coordinator: BudgetBakersDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_transactions_last_7_days"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "BudgetBakers",
            "model": "Wallet API",
            "entry_type": "service",
        }

    @property
    def native_value(self) -> int:
        """Return number of transactions in the last 7 days."""
        return int(self.coordinator.data.get("total_transactions", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        transactions = data.get("transactions", [])
        return {
            ATTR_TOTAL_TRANSACTIONS: data.get("total_transactions", 0),
            ATTR_ACCOUNT_COUNT: data.get("account_count", 0),
            ATTR_ACTIVE_ACCOUNT_IDS: data.get("active_account_ids", []),
            ATTR_REQUESTS_MADE: data.get("requests_made", 0),
            ATTR_UPDATED_AT: _to_iso_string(data.get("updated_at")),
            ATTR_LAST_ERROR: data.get("last_error"),
            ATTR_TRANSACTIONS: transactions[:MAX_TRANSACTIONS_IN_ATTRIBUTES],
        }


def _to_iso_string(value: datetime | None) -> str | None:
    """Return an ISO formatted timestamp with UTC suffix."""
    if value is None:
        return None
    return value.isoformat()
