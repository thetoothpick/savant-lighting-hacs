"""Light platform for Savant Lighting.

Supports setup via Config Entries. Legacy YAML platform setup is kept for
backwards compatibility but is no longer the recommended method.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    LightEntity,
    ColorMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api.client import SavantLightingClient
from .api.light import SavantLight
from . import DOMAIN  # set in __init__.py

_LOGGER = logging.getLogger(__name__)

# Legacy YAML platform schema (deprecated in favor of Config Entries)
try:
    # Home Assistant removed PLATFORM_SCHEMA import in newer versions; protect import usage
    from homeassistant.components.light import PLATFORM_SCHEMA  # type: ignore

    PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
        vol.Required(CONF_HOST): cv.string,
        # vol.Optional(CONF_USERNAME, default='admin'): cv.string,
        # vol.Optional(CONF_PASSWORD): cv.string,
    })
except Exception:  # pragma: no cover - only for forward compatibility
    PLATFORM_SCHEMA = vol.Schema({})


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Legacy YAML setup for Savant Lighting (deprecated).

    Prefer adding the integration via the Home Assistant UI (Config Entries).
    """
    # Assign configuration variables.
    # The configuration check takes care they are present.
    host = config[CONF_HOST]
    # username = config[CONF_USERNAME]
    # password = config.get(CONF_PASSWORD)

    # Setup connection with devices
    client = SavantLightingClient(host)
    client.start()

    for i in range(0, 10):
        if client.client_state.running:
            break
        await asyncio.sleep(1)

    # Verify that passed in configuration works
    if not client.is_connected():
        _LOGGER.error("Could not connect to Savant Lighting host")
        return

    await client.load_lights()

    for i in range(0, 10):
        if client.client_state.loaded_lights:
            break
        await asyncio.sleep(1)

    # Add devices
    async_add_entities(
        SavantLightEntity(client, light) for light in client.registry.lights.values()
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Savant Lighting lights from a config entry."""
    client: SavantLightingClient = hass.data[DOMAIN][entry.entry_id]

    # Load lights list if not already loaded
    if not client.client_state.loaded_lights:
        await client.load_lights()
        for _ in range(0, 20):
            if client.client_state.loaded_lights:
                break
            await asyncio.sleep(0.5)

    # Add entities for all discovered lights
    async_add_entities(
        SavantLightEntity(client, light) for light in client.registry.lights.values()
    )


class SavantLightEntity(LightEntity):
    """Representation of a Savant Light."""

    def __init__(self, client: SavantLightingClient, light: SavantLight) -> None:
        """Initialize a Savant Light."""
        self._client = client
        self._light = light
        self._attr_name = light.name
        self._attr_is_on = None
        self._attr_brightness = None

        if self._light.load[0].min != 100:  # supports brightness
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = None
            self._attr_supported_color_modes = set()

        self._attr_unique_id = light.address

    @property
    def device_info(self) -> DeviceInfo:
        room_name: str = getattr(self._light, 'room', None)
        return DeviceInfo(
            identifiers={('savant_lighting', f'room_{room_name.lower().replace(" ", "_")}')},
            name=room_name,
            suggested_area=room_name
        )

    async def async_turn_on(self, **kwargs: Any):
        """Instruct the light to turn on."""
        brightness = int(kwargs.get(ATTR_BRIGHTNESS, 255) / 255 * 100)
        await self._client.send_light_state(self._light.address, brightness)

    async def async_turn_off(self, **kwargs: Any):
        """Instruct the light to turn off."""
        await self._client.send_light_state(self._light.address, 0)

    async def async_update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        await self._client.load_light_state(self._light.address)
        for i in range(0, 10):
            if self._client.is_light_state_loaded(self._light.address):
                break
            await asyncio.sleep(1)
        if not self._client.is_light_state_loaded(self._light.address):
            return
        self._attr_is_on = self._client.registry.light_on(self._light.address)
        self._attr_brightness = int(self._client.registry.light_brightness(self._light.address) / 100 * 255)
