# Hunter Irrigation

Custom Home Assistant integration for managing Hunter irrigation valves from HA.

## What it does

- Runs configured irrigation zones using `valve` or `switch` entities.
- Uses rain sensors and a binary rain sensor to block watering.
- Honors manual override and simulation inputs.
- Exposes services for start, stop, and preview.
- Preserves compatibility with existing `irrigation.preview_start_request` event-driven scripts.

## Installation

1. Copy the `custom_components/hunter_irrigation` directory into your HA config folder.
2. Add configuration to `configuration.yaml` or include a separate YAML file.

Example:

```yaml
hunter_irrigation: !include irrigation/hunter_irrigation_example.yaml
```

## Services

- `hunter_irrigation.start_zone`
- `hunter_irrigation.stop_zone`
- `hunter_irrigation.preview_zone`

## Compatibility

The integration also listens for the old event `irrigation.preview_start_request` so scripts using the existing preview event can continue to work during migration.

## Example zone configuration

```yaml
hunter_irrigation:
  zones:
    - name: zone_1
      entity_id: valve.travnik_1
      duration_entity: input_number.irrigation_zone_1_duration_min
      duration_min: 15
```
