"""Switch entities for Hunter Irrigation."""
from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HunterIrrigation
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HunterIrrigation = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            HunterRuntimeFlagSwitch(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                key="manual_override",
                icon="mdi:toggle-switch",
            ),
            HunterRuntimeFlagSwitch(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                key="simulate",
                icon="mdi:eye-off",
            ),
            HunterRuntimeFlagSwitch(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                key="manual_rain_block",
                icon="mdi:cloud-lock",
            ),
        ]
    )


class HunterRuntimeFlagSwitch(SwitchEntity):
    """Runtime switch used when external helper entity is not configured."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HunterIrrigation,
        entry_id: str,
        key: str,
        icon: str,
    ) -> None:
        self._coordinator = coordinator
        self._key = key
        self._attr_translation_key = key
        self._attr_icon = icon
        self._attr_unique_id = f"hunter_irrigation_{key}"
        self.entity_id = f"switch.hunter_irrigation_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Hunter Irrigation",
            manufacturer="Hunter",
            model="Irrigation Controller",
        )

    @property
    def is_on(self) -> bool:
        if self._key == "manual_override":
            return self._coordinator.runtime_manual_override
        if self._key == "simulate":
            return self._coordinator.runtime_simulate
        return self._coordinator.runtime_manual_rain_block

    async def async_turn_on(self, **kwargs) -> None:
        _LOGGER.info("[MANUAL] Switch %s turn_on requested", self.entity_id)
        if self._key == "manual_override":
            await self._coordinator.async_set_runtime_manual_override(True)
        elif self._key == "simulate":
            self._coordinator.set_runtime_simulate(True)
        else:
            await self._coordinator.async_set_runtime_manual_rain_block(True)
        self.async_write_ha_state()
        _LOGGER.info("[MANUAL] Switch %s new state: %s", self.entity_id, self.is_on)

    async def async_turn_off(self, **kwargs) -> None:
        _LOGGER.info("[MANUAL] Switch %s turn_off requested", self.entity_id)
        if self._key == "manual_override":
            await self._coordinator.async_set_runtime_manual_override(False)
        elif self._key == "simulate":
            self._coordinator.set_runtime_simulate(False)
        else:
            await self._coordinator.async_set_runtime_manual_rain_block(False)
        self.async_write_ha_state()
        _LOGGER.info("[MANUAL] Switch %s new state: %s", self.entity_id, self.is_on)
