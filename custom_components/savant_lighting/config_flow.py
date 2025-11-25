"""Config flow for Savant Lighting integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST

from . import DOMAIN


class SavantLightingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Savant Lighting."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()

            # Use host as the unique id to avoid duplicate entries per host
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=host, data={CONF_HOST: host})

        data_schema = vol.Schema({vol.Required(CONF_HOST): str})
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
