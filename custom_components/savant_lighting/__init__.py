"""Savant Lighting integration using Config Entries."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api.client import SavantLightingClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "savant_lighting"
PLATFORMS: list[Platform] = [Platform.LIGHT]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Savant Lighting integration (no YAML configuration)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Savant Lighting from a config entry."""
    host = entry.data[CONF_HOST]

    client = SavantLightingClient(host)
    client.start()

    # Wait briefly for the client to connect; if not, defer setup
    for _ in range(0, 20):  # up to ~10 seconds
        if client.client_state.running and client.is_connected():
            break
        await asyncio.sleep(0.5)

    if not client.is_connected():
        _LOGGER.warning("Savant Lighting host is not reachable at %s; retrying later", host)
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    client: SavantLightingClient | None = hass.data[DOMAIN].pop(entry.entry_id, None)
    if client is not None:
        try:
            await client.stop()
        except Exception:  # pragma: no cover - best-effort shutdown
            _LOGGER.debug("Error while stopping Savant client", exc_info=True)
    return unload_ok
