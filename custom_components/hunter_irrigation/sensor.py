"""Sensor entities for Hunter Irrigation."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.components.recorder import history
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import UnitOfPrecipitationDepth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DAILY_RAIN_SENSOR,
    DOMAIN,
    SENSOR_RAIN_GUARD_REASON,
    SENSOR_RAIN_GUARD_STATUS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = [
        HunterRainGuardStatusSensor(entry.entry_id, runtime, "status"),
        HunterRainGuardStatusSensor(entry.entry_id, runtime, "reason"),
    ]

    config = {**entry.data, **entry.options}
    rain = config.get("rain", {})
    daily_rain_sensor = rain.get(CONF_DAILY_RAIN_SENSOR)
    if not daily_rain_sensor:
        _LOGGER.warning("[RAIN] No daily_rain_sensor configured, skipping rain stats")
        async_add_entities(entities)
        return

    _LOGGER.info(f"[RAIN] Setting up coordinator for sensor: {daily_rain_sensor}")
    coordinator = HunterRainStatsCoordinator(hass, daily_rain_sensor)
    
    _LOGGER.info("[RAIN] Calling first_refresh to load data immediately...")
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info(f"[RAIN] First refresh complete. Data: {coordinator.data}")
    except Exception as err:
        _LOGGER.error(f"[RAIN] First refresh FAILED: {err}", exc_info=True)

    entities.extend(
        [
            HunterRainStatSensor(entry.entry_id, coordinator, "rain_yesterday"),
            HunterRainStatSensor(entry.entry_id, coordinator, "rain_day_before_yesterday"),
            HunterRainStatSensor(entry.entry_id, coordinator, "rain_last_7_days_total"),
            HunterRainStatSensor(entry.entry_id, coordinator, "rain_last_24_hours_total"),
            HunterRainStatSensor(entry.entry_id, coordinator, "rain_last_48_hours_total"),
        ]
    )
    async_add_entities(entities)


class HunterRainStatsCoordinator(DataUpdateCoordinator[dict[str, float | None]]):
    """Coordinator computing rainfall rollups from recorder history."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="hunter_irrigation_rain_stats",
            update_interval=timedelta(minutes=1),
        )
        self._entity_id = entity_id
        _LOGGER.info(f"[RAIN] Coordinator initialized for {entity_id}")

    def _sum_cumulative_states(self, states: list[Any]) -> float | None:
        if not states:
            return 0.0
        if len(states) == 1:
            try:
                float(states[0].state)
                return 0.0
            except (TypeError, ValueError):
                return None

        total = 0.0
        prev: float | None = None
        for state in states:
            try:
                current = float(state.state)
            except (TypeError, ValueError):
                continue

            if prev is None:
                prev = current
                continue

            if current >= prev:
                total += current - prev
            else:
                total += current
            prev = current

        return round(total, 2)

    async def _async_get_history_states(self, start: Any, end: Any) -> list[Any]:
        """Read recorder history using proper async API."""
        try:
            _LOGGER.debug(f"[RAIN] Querying history: {self._entity_id} from {start} to {end}")
            
            # Use async_get_significant_states - proper async API
            result = await history.async_get_significant_states(
                self.hass,
                start_time=start,
                end_time=end,
                entity_ids=[self._entity_id],
                include_start_time_state=True,
                significant_changes_only=False,
                no_attributes=True,
            )
            
            if isinstance(result, dict):
                states = result.get(self._entity_id, [])
                _LOGGER.debug(f"[RAIN] Got {len(states)} states for {self._entity_id}")
                return states
            
            _LOGGER.warning(f"[RAIN] Unexpected result type: {type(result)}")
            return []
        except Exception as err:
            _LOGGER.warning(f"[RAIN] Failed to query history: {err}")
            return []

    async def _async_update_data(self) -> dict[str, float | None]:
        now = dt_util.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        start_48h = now - timedelta(hours=48)
        start_24h = now - timedelta(hours=24)

        _LOGGER.info(f"[RAIN] ==== UPDATE START ====")
        _LOGGER.info(f"[RAIN] Entity: {self._entity_id}, Now: {now}")
        _LOGGER.info(f"[RAIN] Query ranges: week({week_start} → {today_start}), 24h({start_24h}), 48h({start_48h})")

        try:
            start_utc = dt_util.as_utc(week_start)
            end_utc = dt_util.as_utc(today_start)

            states = await self._async_get_history_states(start_utc, end_utc)
            _LOGGER.debug(f"[RAIN] Week states count: {len(states)}")
            if states:
                _LOGGER.debug(f"[RAIN]   First: {states[0].state} @ {states[0].last_updated}")
                _LOGGER.debug(f"[RAIN]   Last:  {states[-1].state} @ {states[-1].last_updated}")
            
            states_24h = await self._async_get_history_states(
                dt_util.as_utc(start_24h), dt_util.as_utc(now)
            )
            _LOGGER.debug(f"[RAIN] 24h states count: {len(states_24h)}")
            if states_24h:
                _LOGGER.debug(f"[RAIN]   First: {states_24h[0].state} @ {states_24h[0].last_updated}")
                _LOGGER.debug(f"[RAIN]   Last:  {states_24h[-1].state} @ {states_24h[-1].last_updated}")
            
            states_48h = await self._async_get_history_states(
                dt_util.as_utc(start_48h), dt_util.as_utc(now)
            )
            _LOGGER.debug(f"[RAIN] 48h states count: {len(states_48h)}")
            if states_48h:
                _LOGGER.debug(f"[RAIN]   First: {states_48h[0].state} @ {states_48h[0].last_updated}")
                _LOGGER.debug(f"[RAIN]   Last:  {states_48h[-1].state} @ {states_48h[-1].last_updated}")

            daily_max: dict[Any, float] = {}
            for state in states:
                try:
                    value = float(state.state)
                except (TypeError, ValueError):
                    _LOGGER.debug(f"[RAIN] Skipping invalid state: {state.state}")
                    continue

                local_date = dt_util.as_local(state.last_updated).date()
                previous = daily_max.get(local_date)
                if previous is None or value > previous:
                    daily_max[local_date] = value

            _LOGGER.debug(f"[RAIN] Daily max values: {daily_max}")

            yesterday_date = (today_start - timedelta(days=1)).date()
            day_before_date = (today_start - timedelta(days=2)).date()

            last_7_days_total = 0.0
            for days_back in range(1, 8):
                d = (today_start - timedelta(days=days_back)).date()
                last_7_days_total += float(daily_max.get(d, 0.0))

            rain_24h = self._sum_cumulative_states(states_24h)
            rain_48h = self._sum_cumulative_states(states_48h)

            result = {
                "rain_yesterday": float(daily_max.get(yesterday_date, 0.0)),
                "rain_day_before_yesterday": float(daily_max.get(day_before_date, 0.0)),
                "rain_last_7_days_total": round(last_7_days_total, 2),
                "rain_last_24_hours_total": rain_24h,
                "rain_last_48_hours_total": rain_48h,
            }
            _LOGGER.info(f"[RAIN] RESULT: {result}")
            _LOGGER.info(f"[RAIN] ==== UPDATE END (SUCCESS) ====")
            return result
        except Exception as err:  # pragma: no cover
            _LOGGER.error(f"[RAIN] ==== UPDATE END (FAILED) ====", exc_info=True)
            _LOGGER.error(f"[RAIN] Exception: {err}")
            return {
                "rain_yesterday": None,
                "rain_day_before_yesterday": None,
                "rain_last_7_days_total": None,
                "rain_last_24_hours_total": None,
                "rain_last_48_hours_total": None,
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
        self._attr_entity_id = f"sensor.hunter_irrigation_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Hunter Irrigation",
            manufacturer="Hunter",
            model="Irrigation Controller",
        )

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self._key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid rain stat value: %s", value)
            return None


class HunterRainGuardStatusSensor(SensorEntity):
    """Expose rain guard status and reason for dashboard visibility."""

    _attr_has_entity_name = True

    def __init__(self, entry_id: str, runtime: Any, key: str) -> None:
        self._runtime = runtime
        self._key = key
        self._attr_unique_id = f"hunter_irrigation_rain_guard_{key}"
        self._attr_translation_key = f"rain_guard_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Hunter Irrigation",
            manufacturer="Hunter",
            model="Irrigation Controller",
        )
        if key == "status":
            self._attr_entity_id = SENSOR_RAIN_GUARD_STATUS
        else:
            self._attr_entity_id = SENSOR_RAIN_GUARD_REASON

    @property
    def native_value(self) -> str:
        blocked, rain_state = self._runtime._is_rain_blocked()
        manual_override = self._runtime._is_manual_override()

        if self._key == "status":
            return "povoleno" if manual_override or not blocked else "blokovano"

        if manual_override:
            return "manualni override"

        reason_map = {
            "rain_24h_threshold": "blokovano: srazky za 24 hodin",
            "rain_48h_threshold": "blokovano: srazky za 48 hodin",
            "instant_rain": "blokovano: prave prsi",
            "rain_binary": "blokovano: destovy senzor",
            "daily_threshold_fallback": "blokovano: denni soucet srazek",
            "none": "bez blokace",
        }
        reason = str(rain_state.get("rain_block_reason", "none"))
        return reason_map.get(reason, "bez blokace")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        blocked, rain_state = self._runtime._is_rain_blocked()
        manual_override = self._runtime._is_manual_override()
        return {
            "blocked": blocked,
            "manual_override": manual_override,
            "rain_last_24h": rain_state.get("rain_last_24h"),
            "rain_last_48h": rain_state.get("rain_last_48h"),
            "threshold_24h": rain_state.get("rain_threshold_24h"),
            "threshold_48h": rain_state.get("rain_threshold_48h"),
            "instant_rain": rain_state.get("instant_rain"),
            "daily_rain": rain_state.get("daily_rain"),
        }
