"""Hunter Irrigation custom integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
import voluptuous as vol

from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later

from .const import (
    CONF_DAILY_RAIN_SENSOR,
    CONF_DURATION_ENTITY,
    CONF_DURATION_MIN,
    CONF_INSTANT_RAIN_SENSOR,
    CONF_MANUAL_OVERRIDE_ENTITY,
    CONF_RAIN,
    CONF_RAIN_BINARY_SENSOR,
    CONF_RAIN_THRESHOLD,
    CONF_RAIN_THRESHOLD_48H,
    CONF_RAIN_THRESHOLD_ENTITY,
    CONF_SIMULATE_ENTITY,
    CONF_SKIP_RAIN_CHECK,
    CONF_ZONE,
    CONF_ZONE_ENTITY,
    CONF_ZONES,
    DOMAIN,
    EVENT_OLD_PREVIEW_RESULT,
    EVENT_OLD_START_REQUEST,
    EVENT_PREVIEW_RESULT,
    EVENT_RUN_RESULT,
    SERVICE_PREVIEW_ZONE,
    SERVICE_START_ZONE,
    SERVICE_STOP_ZONE,
    DEFAULT_DURATION_MIN,
    DEFAULT_RAIN_2DAY_THRESHOLD,
    DEFAULT_RAIN_THRESHOLD,
    SENSOR_RAIN_LAST_24H,
    SENSOR_RAIN_LAST_48H,
)

_LOGGER = logging.getLogger(__name__)

START_ZONE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ZONE): cv.string,
        vol.Optional(CONF_ZONE_ENTITY): cv.entity_id,
        vol.Optional(CONF_DURATION_MIN): vol.Coerce(float),
        vol.Optional(CONF_SKIP_RAIN_CHECK, default=False): cv.boolean,
    }
)

STOP_ZONE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ZONE): cv.string,
        vol.Optional(CONF_ZONE_ENTITY): cv.entity_id,
    }
)

PREVIEW_ZONE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ZONE): cv.string,
        vol.Optional(CONF_ZONE_ENTITY): cv.entity_id,
        vol.Optional(CONF_DURATION_MIN): vol.Coerce(float),
    }
)

PLATFORMS = ["number", "sensor", "switch"]


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    config = {**entry.data, **entry.options}
    coordinator = HunterIrrigation(hass, config)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator}

    # Migrate entity IDs first (before platform setup)
    await _async_migrate_entity_ids(hass)
    _LOGGER.info("[SETUP] Entity migration completed")

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_ZONE,
        coordinator.async_handle_start_zone,
        schema=START_ZONE_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_ZONE,
        coordinator.async_handle_stop_zone,
        schema=STOP_ZONE_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PREVIEW_ZONE,
        coordinator.async_handle_preview_zone,
        schema=PREVIEW_ZONE_SERVICE_SCHEMA,
    )

    unsub = hass.bus.async_listen(EVENT_OLD_START_REQUEST, coordinator.async_handle_start_event)
    entry.async_on_unload(unsub)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Hunter Irrigation initialized with %s zones", len(coordinator.zone_by_name))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_migrate_entity_ids(hass: HomeAssistant) -> None:
    """Migrate historical localized entity IDs to stable English object IDs."""
    registry = er.async_get(hass)
    migration_map = {
        "sensor.hunter_irrigation_rain_guard_stav": "sensor.hunter_irrigation_rain_guard_status",
        "sensor.hunter_irrigation_rain_guard_duvod": "sensor.hunter_irrigation_rain_guard_reason",
        "sensor.hunter_irrigation_srazky_za_poslednich_24_hodin": "sensor.hunter_irrigation_rain_last_24_hours_total",
        "sensor.hunter_irrigation_srazky_za_poslednich_48_hodin": "sensor.hunter_irrigation_rain_last_48_hours_total",
        "number.hunter_irrigation_prah_srazek_24_h": "number.hunter_irrigation_rain_threshold_24h",
        "number.hunter_irrigation_rain_threshold": "number.hunter_irrigation_rain_threshold_24h",
        "number.hunter_irrigation_prah_srazek_48_h": "number.hunter_irrigation_rain_threshold_48h",
    }

    _LOGGER.info("[SETUP] Starting entity migration...")
    for old_entity_id, new_entity_id in migration_map.items():
        old_entry = registry.async_get(old_entity_id)
        if old_entry is None:
            _LOGGER.debug(f"[SETUP] {old_entity_id} does not exist, skipping")
            continue
        
        new_entry = registry.async_get(new_entity_id)
        if new_entry is not None:
            _LOGGER.info(f"[SETUP] {new_entity_id} already exists, deleting old {old_entity_id}")
            registry.async_remove(old_entity_id)
            continue
        
        try:
            _LOGGER.info(f"[SETUP] Migrating {old_entity_id} → {new_entity_id}")
            registry.async_update_entity(old_entity_id, new_entity_id=new_entity_id)
            _LOGGER.info(f"[SETUP] Successfully migrated {old_entity_id} → {new_entity_id}")
        except ValueError as err:
            _LOGGER.warning(f"[SETUP] Failed to migrate {old_entity_id} → {new_entity_id}: {err}")


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for service in (SERVICE_START_ZONE, SERVICE_STOP_ZONE, SERVICE_PREVIEW_ZONE):
                hass.services.async_remove(DOMAIN, service)
    return unload_ok


class HunterIrrigation:
    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        self.hass = hass
        self.zone_by_name: dict[str, dict[str, Any]] = {}
        self.zone_by_entity: dict[str, dict[str, Any]] = {}
        self.zone_runtime_duration: dict[str, float] = {}
        for zone in config[CONF_ZONES]:
            name = zone[CONF_NAME]
            self.zone_by_name[name] = zone
            self.zone_by_entity[zone[CONF_ENTITY_ID]] = zone
            self.zone_runtime_duration[name] = float(zone.get(CONF_DURATION_MIN, DEFAULT_DURATION_MIN))

        self.rain_config = config.get(CONF_RAIN, {})
        self.manual_override_entity = config.get(CONF_MANUAL_OVERRIDE_ENTITY)
        self.simulate_entity = config.get(CONF_SIMULATE_ENTITY)
        self.runtime_manual_override = False
        self.runtime_simulate = False
        self.runtime_manual_rain_block = False
        self.runtime_rain_threshold = float(
            self.rain_config.get(CONF_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD)
        )
        self.runtime_rain_threshold_48h = float(
            self.rain_config.get(CONF_RAIN_THRESHOLD_48H, DEFAULT_RAIN_2DAY_THRESHOLD)
        )
        self.active_timers: dict[str, callback] = {}

    def set_zone_runtime_duration(self, zone_name: str, duration_min: float) -> None:
        self.zone_runtime_duration[zone_name] = float(duration_min)

    def set_runtime_manual_override(self, enabled: bool) -> None:
        self.runtime_manual_override = enabled

    def set_runtime_manual_rain_block(self, enabled: bool) -> None:
        """Enable/disable manual rain block for testing without real rainfall."""
        self.runtime_manual_rain_block = enabled
        _LOGGER.info(f"[MANUAL] Manual rain block set to {enabled}")

    def set_runtime_simulate(self, enabled: bool) -> None:
        self.runtime_simulate = enabled

    def set_runtime_rain_threshold(self, threshold_mm: float) -> None:
        self.runtime_rain_threshold = float(threshold_mm)

    def set_runtime_rain_threshold_48h(self, threshold_mm: float) -> None:
        self.runtime_rain_threshold_48h = float(threshold_mm)

    def _get_zone_config(
        self, zone_name: str | None, entity_id: str | None
    ) -> dict[str, Any]:
        if zone_name:
            zone = self.zone_by_name.get(zone_name)
            if not zone:
                raise HomeAssistantError(
                    f"Hunter Irrigation zone '{zone_name}' is not configured"
                )
            return zone

        if entity_id:
            return self.zone_by_entity.get(entity_id, {CONF_ENTITY_ID: entity_id})

        raise HomeAssistantError(
            "Hunter Irrigation service call must include 'zone' or 'zone_entity'"
        )

    def _resolve_duration(self, zone_config: dict[str, Any], override_duration: float | None) -> float:
        if override_duration is not None:
            return float(override_duration)

        duration_entity = zone_config.get(CONF_DURATION_ENTITY)
        if duration_entity:
            state = self.hass.states.get(duration_entity)
            if state and state.state not in ("unknown", "unavailable", "unavailable_due_to_dependencies"):
                try:
                    return float(state.state)
                except (ValueError, TypeError):
                    raise HomeAssistantError(
                        f"Invalid duration value from {duration_entity}: {state.state}"
                    )

        zone_name = zone_config.get(CONF_NAME)
        if zone_name and zone_name in self.zone_runtime_duration:
            return float(self.zone_runtime_duration[zone_name])

        duration_min = zone_config.get(CONF_DURATION_MIN)
        if duration_min is not None:
            return float(duration_min)

        raise HomeAssistantError(
            f"No duration configured for zone {zone_config.get(CONF_NAME, zone_config.get(CONF_ENTITY_ID))}"
        )

    def _read_float_sensor(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if not state or state.state in ("unknown", "unavailable", "unavailable_due_to_dependencies"):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _read_binary_sensor(self, entity_id: str | None) -> bool:
        if not entity_id:
            return False
        return self.hass.states.is_state(entity_id, "on")

    def _is_manual_override(self) -> bool:
        if not self.manual_override_entity:
            return self.runtime_manual_override
        return self.hass.states.is_state(self.manual_override_entity, "on")

    def _is_simulation(self) -> bool:
        if not self.simulate_entity:
            return self.runtime_simulate
        return self.hass.states.is_state(self.simulate_entity, "on")

    def _is_rain_blocked(self) -> tuple[bool, dict[str, Any]]:
        # Check manual rain block first (for testing)
        if self.runtime_manual_rain_block:
            _LOGGER.info("[MANUAL] Manual rain block is ACTIVE (testing mode)")
            return True, {
                "rain_last_24h": None,
                "rain_last_48h": None,
                "daily_rain": None,
                "instant_rain": None,
                "rain_binary": None,
                "rain_threshold_24h": None,
                "rain_threshold_48h": None,
                "rain_threshold_entity": None,
                "rain_block_reason": "manual_rain_block",
            }
        
        rain_last_24h = self._read_float_sensor(SENSOR_RAIN_LAST_24H)
        rain_last_48h = self._read_float_sensor(SENSOR_RAIN_LAST_48H)
        daily = self._read_float_sensor(self.rain_config.get(CONF_DAILY_RAIN_SENSOR))
        instant = self._read_float_sensor(self.rain_config.get(CONF_INSTANT_RAIN_SENSOR))
        binary = self._read_binary_sensor(self.rain_config.get(CONF_RAIN_BINARY_SENSOR))
        threshold_entity = self.rain_config.get(CONF_RAIN_THRESHOLD_ENTITY)
        threshold_from_entity = self._read_float_sensor(threshold_entity)
        if threshold_from_entity is None:
            threshold_from_entity = self._read_float_sensor("number.hunter_irrigation_rain_threshold_24h")
        if threshold_from_entity is None:
                threshold_from_entity = self._read_float_sensor("number.hunter_irrigation_prah_srazek_24_h")
            if threshold_from_entity is None:
                threshold_from_entity = self._read_float_sensor("number.hunter_irrigation_rain_threshold")
        threshold_24h = (
            float(threshold_from_entity)
            if threshold_from_entity is not None
            else self.runtime_rain_threshold
        )
        threshold_48h = self._read_float_sensor("number.hunter_irrigation_prah_srazek_48_h")
        if threshold_48h is None:
            threshold_48h = self._read_float_sensor("number.hunter_irrigation_rain_threshold_48h")
        threshold_48h = float(threshold_48h) if threshold_48h is not None else self.runtime_rain_threshold_48h

        reason = "none"
        blocked = False
        if rain_last_24h is not None and rain_last_24h >= threshold_24h:
            blocked = True
            reason = "rain_24h_threshold"
        elif rain_last_48h is not None and rain_last_48h >= threshold_48h:
            blocked = True
            reason = "rain_48h_threshold"
        elif instant is not None and instant > 0:
            blocked = True
            reason = "instant_rain"
        elif binary:
            blocked = True
            reason = "rain_binary"
        elif daily is not None and daily >= threshold_24h:
            blocked = True
            reason = "daily_threshold_fallback"

        return blocked, {
            "rain_last_24h": rain_last_24h,
            "rain_last_48h": rain_last_48h,
            "daily_rain": daily,
            "instant_rain": instant,
            "rain_binary": binary,
            "rain_threshold_24h": threshold_24h,
            "rain_threshold_48h": threshold_48h,
            "rain_threshold_entity": threshold_entity,
            "rain_block_reason": reason,
        }

    @callback
    def _schedule_zone_close(self, entity_id: str, duration_min: float) -> None:
        if cancel := self.active_timers.pop(entity_id, None):
            cancel()

        @callback
        def _async_close_callback(_: Any) -> None:
            self.active_timers.pop(entity_id, None)
            self.hass.async_create_task(self._async_close_zone(entity_id))

        self.active_timers[entity_id] = async_call_later(
            self.hass, duration_min * 60, _async_close_callback
        )

    async def _async_close_zone(self, entity_id: str) -> None:
        _LOGGER.debug("Closing irrigation entity %s after scheduled runtime", entity_id)
        await self._async_call_switch_service(entity_id, False)

    async def _async_call_switch_service(self, entity_id: str, turn_on: bool) -> None:
        domain = entity_id.split(".", 1)[0]
        if domain == "valve":
            service = "open" if turn_on else "close"
        elif domain == "switch":
            service = "turn_on" if turn_on else "turn_off"
        else:
            service = "open" if turn_on else "close"

        await self.hass.services.async_call(
            domain,
            service,
            {CONF_ENTITY_ID: entity_id},
            blocking=True,
        )

    def _fire_result_event(
        self,
        zone_name: str | None,
        entity_id: str,
        duration_min: float,
        action: str,
        blocked: bool,
        preview: bool,
        simulate: bool,
        manual_override: bool,
        rain_state: dict[str, Any],
    ) -> None:
        event_data = {
            "zone": zone_name,
            "zone_entity": entity_id,
            "duration_min": duration_min,
            "action": action,
            "blocked": blocked,
            "preview": preview,
            "simulate": simulate,
            "manual_override": manual_override,
            **rain_state,
        }
        self.hass.bus.async_fire(EVENT_PREVIEW_RESULT if preview else EVENT_RUN_RESULT, event_data)
        self.hass.bus.async_fire(EVENT_OLD_PREVIEW_RESULT, event_data)

    async def _execute_zone(
        self,
        zone_config: dict[str, Any],
        duration_min: float,
        skip_rain_check: bool,
        preview: bool,
    ) -> None:
        entity_id = zone_config[CONF_ENTITY_ID]
        zone_name = zone_config.get(CONF_NAME)
        manual_override = self._is_manual_override()
        simulate = self._is_simulation()
        blocked, rain_state = self._is_rain_blocked()

        if blocked and not skip_rain_check and not manual_override:
            _LOGGER.info(
                "[BLOCK] Hunter Irrigation blocked by rain for %s: %s",
                entity_id,
                rain_state.get("rain_block_reason"),
            )
            # Suspend automatic watering on the valve
            device_name = entity_id.split(".")[1]
            auto_switch = f"switch.{device_name}_automatic_watering"
            _LOGGER.info(f"[BLOCK] Suspending auto plan: {auto_switch}")
            try:
                await self.hass.services.async_call(
                    "switch",
                    "turn_off",
                    {CONF_ENTITY_ID: auto_switch},
                    blocking=True,
                )
                _LOGGER.info(f"[BLOCK] Auto switch suspended: {auto_switch}")
            except Exception as err:
                _LOGGER.warning(f"[BLOCK] Failed to suspend auto switch {auto_switch}: {err}")
            
            self._fire_result_event(
                zone_name,
                entity_id,
                duration_min,
                "blocked",
                True,
                preview,
                simulate,
                manual_override,
                rain_state,
            )
            return

        if preview or simulate:
            _LOGGER.info(
                "Hunter Irrigation preview %s for %s: duration=%s simulate=%s",
                "request" if preview else "run",
                entity_id,
                duration_min,
                simulate,
            )
            self._fire_result_event(
                zone_name,
                entity_id,
                duration_min,
                "preview" if preview else "simulate",
                False,
                preview,
                simulate,
                manual_override,
                rain_state,
            )
            return

        # Check if we need to resume automatic watering
        if not blocked:
            device_name = entity_id.split(".")[1]
            auto_switch = f"switch.{device_name}_automatic_watering"
            state = self.hass.states.get(auto_switch)
            if state and state.state == "off":
                _LOGGER.info(f"[UNBLOCK] Resuming auto plan: {auto_switch}")
                try:
                    await self.hass.services.async_call(
                        "switch",
                        "turn_on",
                        {CONF_ENTITY_ID: auto_switch},
                        blocking=True,
                    )
                    _LOGGER.info(f"[UNBLOCK] Auto switch resumed: {auto_switch}")
                except Exception as err:
                    _LOGGER.warning(f"[UNBLOCK] Failed to resume auto switch {auto_switch}: {err}")

        await self._async_call_switch_service(entity_id, True)
        self._schedule_zone_close(entity_id, duration_min)

        self._fire_result_event(
            zone_name,
            entity_id,
            duration_min,
            "started",
            False,
            False,
            simulate,
            manual_override,
            rain_state,
        )

    async def async_handle_start_zone(self, call: ServiceCall) -> None:
        zone_config = self._get_zone_config(call.data.get(CONF_ZONE), call.data.get(CONF_ZONE_ENTITY))
        duration_min = self._resolve_duration(zone_config, call.data.get(CONF_DURATION_MIN))
        await self._execute_zone(
            zone_config=zone_config,
            duration_min=duration_min,
            skip_rain_check=call.data.get(CONF_SKIP_RAIN_CHECK, False),
            preview=False,
        )

    async def async_handle_preview_zone(self, call: ServiceCall) -> None:
        zone_config = self._get_zone_config(call.data.get(CONF_ZONE), call.data.get(CONF_ZONE_ENTITY))
        duration_min = self._resolve_duration(zone_config, call.data.get(CONF_DURATION_MIN))
        await self._execute_zone(
            zone_config=zone_config,
            duration_min=duration_min,
            skip_rain_check=True,
            preview=True,
        )

    async def async_handle_stop_zone(self, call: ServiceCall) -> None:
        zone_config = self._get_zone_config(call.data.get(CONF_ZONE), call.data.get(CONF_ZONE_ENTITY))
        entity_id = zone_config[CONF_ENTITY_ID]
        if cancel := self.active_timers.pop(entity_id, None):
            cancel()
        await self._async_call_switch_service(entity_id, False)
        _LOGGER.info("Hunter Irrigation stopped %s", entity_id)

    async def async_handle_start_event(self, event: Any) -> None:
        zone_name = event.data.get(CONF_ZONE)
        entity_id = event.data.get(CONF_ZONE_ENTITY)
        duration = event.data.get(CONF_DURATION_MIN)
        zone_config = self._get_zone_config(zone_name, entity_id)
        duration_min = self._resolve_duration(zone_config, duration)
        await self._execute_zone(
            zone_config=zone_config,
            duration_min=duration_min,
            skip_rain_check=False,
            preview=False,
        )
