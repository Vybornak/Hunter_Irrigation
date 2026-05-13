"""Sensor entities for Hunter Irrigation."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.components.recorder import get_instance, history
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import UnitOfPrecipitationDepth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import CONF_DAILY_RAIN_SENSOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    config = {**entry.data, **entry.options}
    rain = config.get("rain", {})
    daily_rain_sensor = rain.get(CONF_DAILY_RAIN_SENSOR)
    if not daily_rain_sensor:
        return

    coordinator = HunterRainStatsCoordinator(hass, daily_rain_sensor)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            HunterRainStatSensor(entry.entry_id, coordinator, "rain_yesterday"),
            HunterRainStatSensor(entry.entry_id, coordinator, "rain_day_before_yesterday"),
            HunterRainStatSensor(entry.entry_id, coordinator, "rain_last_7_days_total"),
        ]
    )


class HunterRainStatsCoordinator(DataUpdateCoordinator[dict[str, float | None]]):
    """Coordinator computing rainfall rollups from recorder history."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="hunter_irrigation_rain_stats",
            update_interval=timedelta(hours=1),
        )
        self._entity_id = entity_id

    async def _async_update_data(self) -> dict[str, float | None]:
        now = dt_util.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        try:
            start_utc = dt_util.as_utc(week_start)
            end_utc = dt_util.as_utc(today_start)

            def _load_history() -> list[Any]:
                states_by_entity = history.get_significant_states(
                    self.hass,
                    start_utc,
                    end_utc,
                    [self._entity_id],
                    include_start_time_state=False,
                    significant_changes_only=False,
                    minimal_response=True,
                    no_attributes=True,
                )
                return states_by_entity.get(self._entity_id, [])

            states = await get_instance(self.hass).async_add_executor_job(_load_history)

            daily_max: dict[Any, float] = {}
            for state in states:
                try:
                    value = float(state.state)
                except (TypeError, ValueError):
                    continue

                local_date = dt_util.as_local(state.last_updated).date()
                previous = daily_max.get(local_date)
                if previous is None or value > previous:
                    daily_max[local_date] = value

            yesterday_date = (today_start - timedelta(days=1)).date()
            day_before_date = (today_start - timedelta(days=2)).date()

            last_7_days_total = 0.0
            for days_back in range(1, 8):
                d = (today_start - timedelta(days=days_back)).date()
                last_7_days_total += float(daily_max.get(d, 0.0))

            return {
                "rain_yesterday": daily_max.get(yesterday_date),
                "rain_day_before_yesterday": daily_max.get(day_before_date),
                "rain_last_7_days_total": round(last_7_days_total, 2),
            }
        except Exception as err:  # pragma: no cover
            _LOGGER.debug("Failed to calculate rain stats: %s", err)
            return {
                "rain_yesterday": None,
                "rain_day_before_yesterday": None,
                "rain_last_7_days_total": None,
            }


class HunterRainStatSensor(CoordinatorEntity[HunterRainStatsCoordinator], SensorEntity):
    """Rain statistic sensor backed by coordinator data."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_suggested_display_precision = 1
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry_id: str,
        coordinator: HunterRainStatsCoordinator,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"hunter_irrigation_{key}"
        self._attr_translation_key = key
        self.entity_id = f"sensor.hunter_irrigation_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Hunter Irrigation",
            manufacturer="Hunter",
            model="Irrigation Controller",
        )

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self._key) if self.coordinator.data else None
        return float(value) if value is not None else None
