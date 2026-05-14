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
- `number.hunter_irrigation_rain_threshold_24h`
- `number.hunter_irrigation_rain_threshold_48h`
- `switch.hunter_irrigation_manual_override`
- `switch.hunter_irrigation_simulate`
- `switch.hunter_irrigation_manual_rain_block`

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

## 🎨 Dashboard v Home Assistantu

V repozitáři jsou dostupné 2 varianty dashboardu:

### ✨ **DOPORUČENO: `examples/dashboard_modern.yaml` (Moderní design)**

Nový, profesionální dashboard s moderním designem (2026+):

**Funkce:**
- 📊 **Sections layout** - čistá hierarchie a logické seskupení
- 🎯 **Tile cards** - modern, kompaktní, s barevným kódováním
- 💚 **Status na top** - Rain Guard stav (zelená=povoleno, červená=blokováno)
- ⚡ **Quick actions** - Start/Stop tlačítka pro každou zónu
- 📈 **Rain statistics** - 24h, 48h, yesterday, 7 days
- ⏱️ **Watering schedule** - Příští zalévání pro každou zónu
- 🎛️ **Mode controls** - Manual override, simulate, manual rain block
- 🔧 **Settings section** - Thresholds, durations (spodek)
- 📱 **Responsive design** - Funguje na mobilu, tabletu i desktopu

**Instalace:**
1. V Home Assistantu: `Dashboard` → `+ Create new dashboard` → `Create from scratch`
2. Klikni na `Edit dashboard` (tužka ikona) → `Raw configuration editor`
3. Smaž výchozí obsah a vlož obsah z `examples/dashboard_modern.yaml`
4. Klikni `Save`
5. Vůbec nemusíš nic měnit - všechny entity jsou už v integraci připraveny! ✅

---

### 📋 **Alternativa: `examples/dashboard.example.yaml` (Starší design)**

Původní verze s grid-layout (jednodušší, ale méně profesionální).

---

## Vytváření entity ID

Když integraci spustíš, automaticky se vytvoří tyto entity:

```
sensor.hunter_irrigation_rain_guard_status          # Stav rain guard (allow/blocked)
sensor.hunter_irrigation_rain_guard_reason           # Důvod blokace
sensor.hunter_irrigation_rain_yesterday              # Včera (mm)
sensor.hunter_irrigation_rain_day_before_yesterday   # Předvčíra (mm)
sensor.hunter_irrigation_rain_last_7_days_total     # Posledních 7 dní (mm)
sensor.hunter_irrigation_rain_last_24_hours_total   # Posledních 24h (mm) ⭐
sensor.hunter_irrigation_rain_last_48_hours_total   # Posledních 48h (mm) ⭐
sensor.travnik_1_next_cycle                         # Příští zalévání Z1
sensor.travnik_2_next_cycle                         # Příští zalévání Z2
sensor.travnik_3_next_cycle                         # Příští zalévání Z3

number.hunter_irrigation_zone_1_duration            # Délka Z1 (min)
number.hunter_irrigation_zone_2_duration            # Délka Z2 (min)
number.hunter_irrigation_zone_3_duration            # Délka Z3 (min)
number.hunter_irrigation_rain_threshold_24h         # Prah 24h (mm)
number.hunter_irrigation_rain_threshold_48h         # Prah 48h (mm)

switch.hunter_irrigation_manual_override            # Ignoruj déšť
switch.hunter_irrigation_simulate                   # Bez fyzického otevření
switch.hunter_irrigation_manual_rain_block          # TEST: Blokuj bez srážek
```

✨ Všechny entity jsou již připravené k použití - **nemusíš ručně nic vytvářet!**

---

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
