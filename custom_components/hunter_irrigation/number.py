"""Number entities for Hunter Irrigation."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfPrecipitationDepth, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
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
        entities.append(HunterZoneDurationNumber(coordinator, entry.entry_id, zone_name))

    entities.append(HunterRainThreshold24hNumber(coordinator, entry.entry_id))
    entities.append(HunterRainThreshold48hNumber(coordinator, entry.entry_id))
    async_add_entities(entities)


class HunterBaseNumberEntity(NumberEntity):
    """Base number entity with shared device metadata."""

    _attr_has_entity_name = True

    def __init__(self, entry_id: str) -> None:
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Hunter Irrigation",
            manufacturer="Hunter",
            model="Irrigation Controller",
        )


class HunterZoneDurationNumber(HunterBaseNumberEntity):
    """Runtime zone duration in minutes."""

    _attr_icon = "mdi:timer"
    _attr_native_min_value = 1
    _attr_native_max_value = 240
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator: HunterIrrigation, entry_id: str, zone_name: str) -> None:
        super().__init__(entry_id)
        self._coordinator = coordinator
        self._zone_name = zone_name
        zone_slug = slugify(zone_name)
        self._attr_unique_id = f"hunter_irrigation_{zone_slug}_duration_min"
        self._attr_translation_key = "zone_duration"
        self._attr_translation_placeholders = {"zone_name": zone_name}
        self._attr_entity_id = f"number.hunter_irrigation_{zone_slug}_duration"

    @property
    def native_value(self) -> float:
        return self._coordinator.zone_runtime_duration.get(self._zone_name, 15.0)

    async def async_set_native_value(self, value: float) -> None:
        self._coordinator.set_zone_runtime_duration(self._zone_name, float(value))
        self.async_write_ha_state()


class HunterRainThreshold24hNumber(HunterBaseNumberEntity):
    """Runtime rain threshold for rolling 24h window."""

    _attr_icon = "mdi:weather-rainy"
    _attr_native_min_value = 0
    _attr_native_max_value = 50
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS

    def __init__(self, coordinator: HunterIrrigation, entry_id: str) -> None:
        super().__init__(entry_id)
        self._coordinator = coordinator
        self._attr_unique_id = "hunter_irrigation_rain_threshold_24h_mm"
        self._attr_translation_key = "rain_threshold_24h"
        self._attr_entity_id = "number.hunter_irrigation_rain_threshold_24h"

    @property
    def native_value(self) -> float:
        return self._coordinator.runtime_rain_threshold

    async def async_set_native_value(self, value: float) -> None:
        self._coordinator.set_runtime_rain_threshold(float(value))
        self.async_write_ha_state()


class HunterRainThreshold48hNumber(HunterBaseNumberEntity):
    """Runtime rain threshold for rolling 48h window."""

    _attr_icon = "mdi:weather-pouring"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS

    def __init__(self, coordinator: HunterIrrigation, entry_id: str) -> None:
        super().__init__(entry_id)
        self._coordinator = coordinator
        self._attr_unique_id = "hunter_irrigation_rain_threshold_48h_mm"
        self._attr_translation_key = "rain_threshold_48h"
        self._attr_entity_id = "number.hunter_irrigation_rain_threshold_48h"

    @property
    def native_value(self) -> float:
        return self._coordinator.runtime_rain_threshold_48h

    async def async_set_native_value(self, value: float) -> None:
        self._coordinator.set_runtime_rain_threshold_48h(float(value))
        self.async_write_ha_state()
