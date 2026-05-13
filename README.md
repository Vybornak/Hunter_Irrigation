# Hunter Irrigation

Custom Home Assistant integration for controlling Hunter irrigation zones from Home Assistant.

## Features

- Control irrigation zones using `valve` or `switch` entities
- Rain blocking logic (daily sensor, instant sensor, binary rain sensor)
- Manual override and simulation mode support
- Services:
  - `hunter_irrigation.start_zone`
  - `hunter_irrigation.stop_zone`
  - `hunter_irrigation.preview_zone`
- Backward compatibility with `irrigation.preview_start_request`

## Repository layout

- `custom_components/hunter_irrigation/` integration code
- `examples/configuration.example.yaml` example YAML config
- `hacs.json` metadata for HACS custom repository

## Installation via HACS (Custom repository)

1. Push this repository to GitHub.
2. In HACS go to `Integrations` -> menu -> `Custom repositories`.
3. Add your repo URL and choose category `Integration`.
4. Install `Hunter Irrigation` and restart Home Assistant.
5. Add YAML config (see `examples/configuration.example.yaml`).

## YAML configuration

```yaml
hunter_irrigation:
  zones:
    - name: zone_1
      entity_id: valve.travnik_1
      duration_entity: input_number.irrigation_zone_1_duration_min
      duration_min: 15
    - name: zone_2
      entity_id: valve.travnik_2
      duration_entity: input_number.irrigation_zone_2_duration_min
      duration_min: 15
    - name: zone_3
      entity_id: valve.travnik_3
      duration_entity: input_number.irrigation_zone_3_duration_min
      duration_min: 15

  rain:
    daily_rain_sensor: sensor.weather_station_sws_12500_denni_uhrn_srazek
    instant_rain_sensor: sensor.weather_station_sws_12500_srazky
    rain_binary_sensor: binary_sensor.vyborny_premyslovice_destovy_senzor
    threshold_mm: 2.0

  manual_override: input_boolean.irrigation_manual_override
  simulate: input_boolean.irrigation_simulate
```
