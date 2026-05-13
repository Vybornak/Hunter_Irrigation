"""Number entities for Hunter Irrigation."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfPrecipitationDepth, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from . import HunterIrrigation
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HunterIrrigation = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[NumberEntity] = []

    for zone_name in coordinator.zone_by_name:
        entities.append(HunterZoneDurationNumber(coordinator, zone_name))

    entities.append(HunterRainThresholdNumber(coordinator))
    async_add_entities(entities)


class HunterZoneDurationNumber(NumberEntity):
    """Runtime zone duration in minutes."""

    _attr_icon = "mdi:timer"
    _attr_native_min_value = 1
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator: HunterIrrigation, zone_name: str) -> None:
        self._coordinator = coordinator
        self._zone_name = zone_name
        zone_slug = slugify(zone_name)
        self._attr_unique_id = f"hunter_irrigation_{zone_slug}_duration_min"
        self._attr_name = f"Hunter Irrigation {zone_name} duration"
        self.entity_id = f"number.hunter_irrigation_{zone_slug}_duration"

    @property
    def native_value(self) -> float:
        return self._coordinator.zone_runtime_duration.get(self._zone_name, 15.0)

    async def async_set_native_value(self, value: float) -> None:
        self._coordinator.set_zone_runtime_duration(self._zone_name, float(value))
        self.async_write_ha_state()


class HunterRainThresholdNumber(NumberEntity):
    """Runtime rain threshold in mm/day."""

    _attr_icon = "mdi:weather-rainy"
    _attr_native_min_value = 0
    _attr_native_max_value = 50
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS

    def __init__(self, coordinator: HunterIrrigation) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = "hunter_irrigation_rain_threshold_mm"
        self._attr_name = "Hunter Irrigation rain threshold"
        self.entity_id = "number.hunter_irrigation_rain_threshold"

    @property
    def native_value(self) -> float:
        return self._coordinator.runtime_rain_threshold

    async def async_set_native_value(self, value: float) -> None:
        self._coordinator.set_runtime_rain_threshold(float(value))
        self.async_write_ha_state()
