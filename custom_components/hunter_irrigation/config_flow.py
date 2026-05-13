"""Config flow for Hunter Irrigation."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.helpers import selector

from .const import (
    CONF_DAILY_RAIN_SENSOR,
    CONF_DURATION_MIN,
    CONF_INSTANT_RAIN_SENSOR,
    CONF_RAIN,
    CONF_RAIN_BINARY_SENSOR,
    CONF_RAIN_THRESHOLD,
    CONF_ZONES,
    DEFAULT_DURATION_MIN,
    DEFAULT_RAIN_THRESHOLD,
    DOMAIN,
)

CONF_ZONE_COUNT = "zone_count"


def _zone_schema(
    default_name: str = "",
    default_entity: str | None = None,
    default_duration: float = DEFAULT_DURATION_MIN,
) -> vol.Schema:
    entity_kwargs: dict[str, Any] = {}
    if default_entity:
        entity_kwargs["default"] = default_entity
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=default_name): selector.TextSelector(),
            vol.Required(CONF_ENTITY_ID, **entity_kwargs): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["switch", "valve", "input_boolean"])
            ),
            vol.Required(CONF_DURATION_MIN, default=default_duration): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=240, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
    )


def _rain_schema(rain: dict[str, Any] | None = None) -> vol.Schema:
    rain = rain or {}
    schema: dict[Any, Any] = {}
    for key, domain in [
        (CONF_DAILY_RAIN_SENSOR, "sensor"),
        (CONF_INSTANT_RAIN_SENSOR, "sensor"),
        (CONF_RAIN_BINARY_SENSOR, "binary_sensor"),
    ]:
        existing = rain.get(key)
        if existing:
            schema[vol.Optional(key, default=existing)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain=domain)
            )
        else:
            schema[vol.Optional(key)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain=domain)
            )
    schema[
        vol.Required(
            CONF_RAIN_THRESHOLD,
            default=float(rain.get(CONF_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD)),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, max=50, step=0.1, mode=selector.NumberSelectorMode.BOX
        )
    )
    return vol.Schema(schema)


def _user_schema(default_count: int = 3) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ZONE_COUNT, default=default_count): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=8, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
    )


class HunterIrrigationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Hunter Irrigation."""

    VERSION = 1

    def __init__(self) -> None:
        self._zones: list[dict[str, Any]] = []
        self._zone_count = 0
        self._current_zone = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._zone_count = int(user_input[CONF_ZONE_COUNT])
            self._current_zone = 1
            return await self.async_step_zone()

        return self.async_show_form(step_id="user", data_schema=_user_schema())

    async def async_step_zone(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._zones.append(
                {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_ENTITY_ID: user_input[CONF_ENTITY_ID],
                    CONF_DURATION_MIN: float(user_input[CONF_DURATION_MIN]),
                }
            )
            self._current_zone += 1

        if self._current_zone > self._zone_count:
            return await self.async_step_rain()

        return self.async_show_form(
            step_id="zone",
            data_schema=_zone_schema(default_name=f"zone_{self._current_zone}"),
            description_placeholders={
                "zone_num": str(self._current_zone),
                "zone_count": str(self._zone_count),
            },
        )

    async def async_step_rain(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            rain: dict[str, Any] = {
                CONF_RAIN_THRESHOLD: float(user_input[CONF_RAIN_THRESHOLD])
            }
            for key in (CONF_DAILY_RAIN_SENSOR, CONF_INSTANT_RAIN_SENSOR, CONF_RAIN_BINARY_SENSOR):
                val = user_input.get(key)
                if val:
                    rain[key] = val

            return self.async_create_entry(
                title="Hunter Irrigation",
                data={CONF_ZONES: self._zones, CONF_RAIN: rain},
            )

        return self.async_show_form(step_id="rain", data_schema=_rain_schema())

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HunterIrrigationOptionsFlow:
        return HunterIrrigationOptionsFlow(config_entry)


class HunterIrrigationOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Hunter Irrigation."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config: dict[str, Any] = {**config_entry.data, **config_entry.options}
        self._existing_zones: list[dict[str, Any]] = list(
            self._config.get(CONF_ZONES, [])
        )
        self._zones: list[dict[str, Any]] = []
        self._zone_count = 0
        self._current_zone = 0

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._zone_count = int(user_input[CONF_ZONE_COUNT])
            self._current_zone = 1
            return await self.async_step_zone()

        return self.async_show_form(
            step_id="init",
            data_schema=_user_schema(default_count=len(self._existing_zones)),
        )

    async def async_step_zone(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._zones.append(
                {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_ENTITY_ID: user_input[CONF_ENTITY_ID],
                    CONF_DURATION_MIN: float(user_input[CONF_DURATION_MIN]),
                }
            )
            self._current_zone += 1

        if self._current_zone > self._zone_count:
            return await self.async_step_rain()

        idx = self._current_zone - 1
        existing = self._existing_zones[idx] if idx < len(self._existing_zones) else {}

        return self.async_show_form(
            step_id="zone",
            data_schema=_zone_schema(
                default_name=existing.get(CONF_NAME, f"zone_{self._current_zone}"),
                default_entity=existing.get(CONF_ENTITY_ID),
                default_duration=float(existing.get(CONF_DURATION_MIN, DEFAULT_DURATION_MIN)),
            ),
            description_placeholders={
                "zone_num": str(self._current_zone),
                "zone_count": str(self._zone_count),
            },
        )

    async def async_step_rain(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            rain: dict[str, Any] = {
                CONF_RAIN_THRESHOLD: float(user_input[CONF_RAIN_THRESHOLD])
            }
            for key in (CONF_DAILY_RAIN_SENSOR, CONF_INSTANT_RAIN_SENSOR, CONF_RAIN_BINARY_SENSOR):
                val = user_input.get(key)
                if val:
                    rain[key] = val

            return self.async_create_entry(
                title="",
                data={CONF_ZONES: self._zones, CONF_RAIN: rain},
            )

        existing_rain = self._config.get(CONF_RAIN, {})
        return self.async_show_form(
            step_id="rain",
            data_schema=_rain_schema(existing_rain),
        )
