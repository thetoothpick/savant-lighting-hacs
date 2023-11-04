"""Platform for light integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (ATTR_BRIGHTNESS, PLATFORM_SCHEMA,
                                            LightEntity, ATTR_BRIGHTNESS_PCT, ColorMode)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api.client import SavantLightingClient
from .api.light import SavantLight

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    # vol.Optional(CONF_USERNAME, default='admin'): cv.string,
    # vol.Optional(CONF_PASSWORD): cv.string,
})


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    host = config[CONF_HOST]
    # username = config[CONF_USERNAME]
    # password = config.get(CONF_PASSWORD)

    # Setup connection with devices
    client = SavantLightingClient(host)
    # hass.async_create_task(client.run())
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
    async_add_entities(SavantLightEntity(client, light) for light in client.registry.lights.values())


class SavantLightEntity(LightEntity):
    """Representation of a Savant Light."""

    def __init__(self, client: SavantLightingClient, light: SavantLight) -> None:
        """Initialize a Savant Light."""
        self._client = client
        self._light = light
        self._attr_name = light.name
        self._attr_is_on = None
        self._attr_brightness = None

        self._attr_unique_id = f"savant_light_{light.address}"

        if self._light.load[0].min != 100:  # supports brightness
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

        self._attr_unique_id = light.address

        self._attr_device_info = DeviceInfo(name=light.name, suggested_area=light.room)

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
        while not self._client.is_light_state_loaded(self._light.address):
            await asyncio.sleep(1)
        self._attr_is_on = self._client.registry.light_on(self._light.address)
        self._attr_brightness = int(self._client.registry.light_brightness(self._light.address) / 100 * 255)
