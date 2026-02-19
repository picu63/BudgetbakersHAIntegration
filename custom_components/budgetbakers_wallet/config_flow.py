"""Config flow for BudgetBakers Wallet integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BudgetBakersApiClient, BudgetBakersApiError, BudgetBakersAuthError
from .const import CONF_TOKEN, DEFAULT_NAME, DOMAIN


class BudgetBakersConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BudgetBakers Wallet."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            )

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        token = user_input[CONF_TOKEN].strip()

        if not token:
            errors["base"] = "invalid_auth"
        else:
            session = async_get_clientsession(self.hass)
            api_client = BudgetBakersApiClient(session, token)
            try:
                await api_client.validate_token()
            except BudgetBakersAuthError:
                errors["base"] = "invalid_auth"
            except BudgetBakersApiError:
                errors["base"] = "cannot_connect"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
                errors=errors,
            )

        return self.async_create_entry(title=DEFAULT_NAME, data={CONF_TOKEN: token})

    async def async_step_reauth(self, _: dict[str, Any]) -> config_entries.FlowResult:
        """Handle initiation of re-authentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Handle re-authentication confirmation."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            )

        entries = self.hass.config_entries.async_entries(DOMAIN)
        if not entries:
            return self.async_abort(reason="reauth_unsuccessful")

        token = user_input[CONF_TOKEN].strip()
        if not token:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
                errors={"base": "invalid_auth"},
            )

        session = async_get_clientsession(self.hass)
        api_client = BudgetBakersApiClient(session, token)

        try:
            await api_client.validate_token()
        except BudgetBakersAuthError:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
                errors={"base": "invalid_auth"},
            )
        except BudgetBakersApiError:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
                errors={"base": "cannot_connect"},
            )

        entry = entries[0]
        self.hass.config_entries.async_update_entry(entry, data={CONF_TOKEN: token})
        await self.hass.config_entries.async_reload(entry.entry_id)
        return self.async_abort(reason="reauth_successful")
