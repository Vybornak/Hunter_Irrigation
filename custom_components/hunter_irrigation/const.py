"""Constants for the Hunter Irrigation custom integration."""

DOMAIN = "hunter_irrigation"
CONF_ZONES = "zones"
CONF_DURATION_ENTITY = "duration_entity"
CONF_DURATION_MIN = "duration_min"
CONF_RAIN = "rain"
CONF_DAILY_RAIN_SENSOR = "daily_rain_sensor"
CONF_INSTANT_RAIN_SENSOR = "instant_rain_sensor"
CONF_RAIN_BINARY_SENSOR = "rain_binary_sensor"
CONF_RAIN_THRESHOLD = "threshold_mm"
CONF_RAIN_THRESHOLD_ENTITY = "threshold_entity"
CONF_MANUAL_OVERRIDE_ENTITY = "manual_override"
CONF_SIMULATE_ENTITY = "simulate"
CONF_SKIP_RAIN_CHECK = "skip_rain_check"
CONF_ZONE = "zone"
CONF_ZONE_ENTITY = "zone_entity"

SERVICE_START_ZONE = "start_zone"
SERVICE_STOP_ZONE = "stop_zone"
SERVICE_PREVIEW_ZONE = "preview_zone"

EVENT_PREVIEW_RESULT = "hunter_irrigation.preview_result"
EVENT_RUN_RESULT = "hunter_irrigation.run_result"
EVENT_OLD_PREVIEW_RESULT = "irrigation.preview_result"
EVENT_OLD_START_REQUEST = "irrigation.preview_start_request"

DEFAULT_DURATION_MIN = 15.0
DEFAULT_RAIN_THRESHOLD = 10.0
DEFAULT_RAIN_2DAY_THRESHOLD = 25.0

SENSOR_RAIN_LAST_24H = f"sensor.{DOMAIN}_rain_last_24_hours_total"
SENSOR_RAIN_LAST_48H = f"sensor.{DOMAIN}_rain_last_48_hours_total"
SENSOR_RAIN_GUARD_STATUS = f"sensor.{DOMAIN}_rain_guard_status"
SENSOR_RAIN_GUARD_REASON = f"sensor.{DOMAIN}_rain_guard_reason"
