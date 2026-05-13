"""Switch entities for Hunter Irrigation."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HunterIrrigation
from .const import DOMAIN


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    data = hass.data.get(DOMAIN)
    if not data:
        return

    coordinator: HunterIrrigation = data["coordinator"]
    async_add_entities(
        [
            HunterRuntimeFlagSwitch(
                coordinator=coordinator,
                key="manual_override",
                name="Hunter Irrigation manual override",
                icon="mdi:toggle-switch",
            ),
            HunterRuntimeFlagSwitch(
                coordinator=coordinator,
                key="simulate",
                name="Hunter Irrigation simulation",
                icon="mdi:eye-off",
            ),
        ]
    )


class HunterRuntimeFlagSwitch(SwitchEntity):
    """Runtime switch used when external helper entity is not configured."""

    def __init__(self, coordinator: HunterIrrigation, key: str, name: str, icon: str) -> None:
        self._coordinator = coordinator
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"hunter_irrigation_{key}"
        self.entity_id = f"switch.hunter_irrigation_{key}"

    @property
    def is_on(self) -> bool:
        if self._key == "manual_override":
            return self._coordinator.runtime_manual_override
        return self._coordinator.runtime_simulate

    async def async_turn_on(self, **kwargs) -> None:
        if self._key == "manual_override":
            self._coordinator.set_runtime_manual_override(True)
        else:
            self._coordinator.set_runtime_simulate(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        if self._key == "manual_override":
            self._coordinator.set_runtime_manual_override(False)
        else:
            self._coordinator.set_runtime_simulate(False)
        self.async_write_ha_state()
