# Hunter Irrigation

Vlastní integrace pro Home Assistant pro řízení ventilů závlahy Hunter.

## Co dělá

- Spouští nakonfigurované zóny přes entity typu `valve` nebo `switch`.
- Automaticky vytváří vlastní ovládací entity (`number` a `switch`) pro dashboard.
- Blokuje zálivku podle srážkových senzorů a dešťového binárního senzoru.
- Umožňuje nastavit práh deště i dynamicky přes helper `input_number`.
- Umožňuje použít externí `manual_override` a `simulate` helpery (volitelné).
- Nabízí služby pro start, stop a preview.
- Zachovává kompatibilitu se stávajícími skripty používajícími událost `irrigation.preview_start_request`.

## Instalace

1. Zkopirujte slozku `custom_components/hunter_irrigation` do konfigurace Home Assistantu.
2. Přidejte konfiguraci do `configuration.yaml` nebo ji načtěte z externího YAML souboru.

Příklad:

```yaml
hunter_irrigation: !include irrigation/hunter_irrigation_example.yaml
```

## Služby

- `hunter_irrigation.start_zone`
- `hunter_irrigation.stop_zone`
- `hunter_irrigation.preview_zone`

## Kompatibilita

Integrace také naslouchá starší události `irrigation.preview_start_request`, aby při migraci dál fungovaly původní skripty.

## Příklad konfigurace zóny

```yaml
hunter_irrigation:
  zones:
    - name: zone_1
      entity_id: valve.travnik_1
      duration_min: 15
```

## Vestavěné entity

Pokud helpery nenastavíte, integrace použije vestavěné entity:

- `number.hunter_irrigation_zone_1_duration`
- `number.hunter_irrigation_zone_2_duration`
- `number.hunter_irrigation_zone_3_duration`
- `number.hunter_irrigation_rain_threshold`
- `switch.hunter_irrigation_manual_override`
- `switch.hunter_irrigation_simulation`

## Doporučené externí helpery (volitelné)

- `input_number.irrigation_zone_1_duration_min`
- `input_number.irrigation_zone_2_duration_min`
- `input_number.irrigation_zone_3_duration_min`
- `input_number.irrigation_rain_threshold_mm`
- `input_boolean.irrigation_manual_override`
- `input_boolean.irrigation_simulate`
