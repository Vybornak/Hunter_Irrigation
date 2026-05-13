# Hunter Irrigation

Vlastní integrace pro Home Assistant pro řízení závlahy Hunter.

## Co integrace umí

- Spouštět závlahové zóny přes entity typu `valve` nebo `switch`
- Automaticky vytvářet ovládací entity (`number` a `switch`) bez ručního zakládání helperů
- Blokovat zálivku podle srážek:
  - denní úhrn (`daily_rain_sensor`)
  - okamžité srážky (`instant_rain_sensor`)
  - dešťový binární senzor (`rain_binary_sensor`)
- Respektovat ruční přepsání (`manual_override`) a simulační režim (`simulate`)
- Poskytovat služby:
  - `hunter_irrigation.start_zone`
  - `hunter_irrigation.stop_zone`
  - `hunter_irrigation.preview_zone`
- Udržet zpětnou kompatibilitu s událostí `irrigation.preview_start_request`

## Struktura repozitare

- `custom_components/hunter_irrigation/` kód integrace
- `examples/configuration.example.yaml` ukázka konfigurace
- `examples/helpers.example.yaml` ukázka helperů (`input_number`, `input_boolean`)
- `examples/dashboard.example.yaml` ukázka Lovelace dashboardu
- `CHANGELOG.md` historie změn pro release notes
- `hacs.json` metadata pro HACS

## Instalace přes HACS (vlastní repozitář)

1. Nahrajte tento repozitář na GitHub.
2. V HACS otevřete `Integrations` -> menu -> `Custom repositories`.
3. Přidejte URL repozitáře a zvolte kategorii `Integration`.
4. Nainstalujte `Hunter Irrigation` a restartujte Home Assistant.
5. Přidejte YAML konfiguraci (viz `examples/configuration.example.yaml`).

## Automaticky vytvořené entity

Po načtení integrace se vytvoří entity, které můžeš hned použít v dashboardu:

- `number.hunter_irrigation_zone_1_duration`
- `number.hunter_irrigation_zone_2_duration`
- `number.hunter_irrigation_zone_3_duration`
- `number.hunter_irrigation_rain_threshold`
- `switch.hunter_irrigation_manual_override`
- `switch.hunter_irrigation_simulation`

Ruční helpery tedy nejsou povinné.

## Volitelné externí helpery

Pokud chceš zachovat původní helper entity (`input_number.*`, `input_boolean.*`), můžeš je stále použít.
Ukázka je v `examples/helpers.example.yaml`.

## YAML konfigurace

```yaml
hunter_irrigation:
  zones:
    - name: zone_1
      entity_id: valve.travnik_1
      duration_min: 15
    - name: zone_2
      entity_id: valve.travnik_2
      duration_min: 15
    - name: zone_3
      entity_id: valve.travnik_3
      duration_min: 15

  rain:
    daily_rain_sensor: sensor.weather_station_sws_12500_denni_uhrn_srazek
    instant_rain_sensor: sensor.weather_station_sws_12500_srazky
    rain_binary_sensor: binary_sensor.vyborny_premyslovice_destovy_senzor
    threshold_mm: 2.0
```

## Dashboard v Home Assistantu

Ano, může to být rovnou součástí repozitáře. Integrace sama o sobě zatím dashboard automaticky nevytvoří, ale v repozitáři je připravená šablona:

- `examples/dashboard.example.yaml`

Postup je jednoduchý:

1. V Home Assistantu vytvořte novou dashboard záložku.
2. Zvolte `Raw configuration editor`.
3. Vložte obsah z `examples/dashboard.example.yaml`.
4. Upravte hlavně zóny a srážkové senzory podle vašich skutečných `entity_id`.

Šablona obsahuje:

- přehled stavu (manual override, simulace, déšť)
- ovládání prahu deště
- ovládání zón (spuštění/zastavení)
- nastavování délky zálivky
- diagnostiku srážkových senzorů

## Release proces (HACS update + changelog)

Když budeš chtít vydat novou verzi, provedeme vždy stejný postup:

1. Doplnit novou sekci verze do `CHANGELOG.md`.
2. Commit + push do `main`.
3. Ověřit přihlášení GitHub CLI:
  - `gh auth status`
4. Spustit release workflow přes CLI:
  - `gh workflow run release.yml -f version=1.0.4 -f prerelease=false`
5. Ověřit běh workflow:
  - `gh run list --workflow release.yml --limit 1`
  - `gh run view <run_id>`
6. Po dokončení workflow zkontrolovat release:
  - `gh release view 1.0.4`
7. V HACS spustit `Check for updates` (nebo počkat na refresh cache).

Poznámka: Verzi v `manifest.json`, git tag i GitHub Release vytváří release workflow automaticky.
Poznámka: Právě release notes z GitHub Release se zobrazují v HACS/HA u dané verze.
