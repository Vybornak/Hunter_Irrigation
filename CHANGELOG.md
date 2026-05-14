# Seznam změn

V tomto souboru jsou evidovány všechny důležité změny projektu.

Formát vychází z Keep a Changelog a Semantic Versioning.

## [Nevydáno]

## [1.0.31] - 2026-05-14

### Změněno
- Dashboard: přesunuty informace o dalších cyklech a stavu do badges, odstraněny nastavení blokace.
- Opravena česká diakritika v dashboard příkladě.

## [1.0.30] - 2026-05-14

### Opraveno
- Vrácena správná implementace `_iter_zone_auto_switches()` pro správné hledání `_automatic_watering` switch.
- Vrácena správná implementace `_async_call_switch_service()` pro správné rozlišení domain (valve vs switch).
- Opraveny chyby z 1.0.29 (manuální blokace a spuštění zón).

## [1.0.29] - 2026-05-14

### Opraveno
- Service call pro spuštění/zastavení zón nyní používá `switch` služby namísto neexistujícího `valve.open`.

## [1.0.28] - 2026-05-14

### Opraveno
- Chyba v entity_id konstrukci u manuální blokace deště: entity se správně vrací bez zdvojení sufixu `_automatic_watering`.

## [1.0.27] - 2026-05-14

### Opraveno
- Vydaná verze je nyní čistý patch release navázaný na aktuální tag bez přepisování už publikovaného releasu.

### Změněno
- Release proces je doplněn o pravidlo, že už publikovaný tag se nemá retagovat; při potřebě opravy se má použít nová patch verze.

## [1.0.26] - 2026-05-14

### Opraveno
- Ruční blokace deště si nyní pamatuje jen ty `switch.<zona>_automatic_watering`, které sama vypnula, a při odblokování vrací zpět pouze je.
- Po vypnutí ruční blokace se obnoví automatické zavlažování jen u skutečně suspendovaných zón, bez přepisování nezávislých ručních stavů.

### Změněno
- Dashboard example je zjednodušený: horní badges už neobsahují duplicitní rain statistiky, další cykly jsou přesunuté hned pod badges a srážkové přehledy jsou v samostatné sekci.

## [1.0.25] - 2026-05-14

### Opraveno
- Ruční blokace deště nyní při zapnutí okamžitě aplikuje blokaci do praxe:
	- vypne `switch.<zona>_automatic_watering` pro všechny zóny,
	- pokud už zóna běží, ihned ji zastaví,
	- zruší aktivní runtime timer dané zóny.

### Přidáno
- Detailní diagnostické logování pro ruční blokaci deště (`[MANUAL]`):
	- požadavek na zapnutí/vypnutí switch entity,
	- seznam cílových auto switchů,
	- stav auto switchů před/po service call,
	- varování, pokud cílový auto switch neexistuje,
	- logování okamžitého zastavení běžící zóny.

## [1.0.24] - 2026-05-14

### Opraveno
- Hodnoty `number.hunter_irrigation_rain_threshold_24h` a `number.hunter_irrigation_rain_threshold_48h` se nyní perzistentně ukládají do options config entry, takže po restartu zůstávají zachovány.
- `switch.hunter_irrigation_manual_rain_block` nyní okamžitě aplikuje blokaci v praxi: při zapnutí vypne auto zavlažování zón, při vypnutí ho opět zapne.

### Změněno
- Number entity settery pro thresholdy používají asynchronní persistenci runtime hodnot.

## [1.0.23] - 2026-05-14

### Opraveno
- Opraven `IndentationError` v `__init__.py`, který způsoboval pád Hassfest validace.
- Dokončeno vydání po úspěšné CI validaci, aby byla nová verze dostupná v distribuci.

### Stabilizováno
- Release pipeline je nyní spouštěna z funkčního `gh` CLI prostředí.

## [1.0.22] - 2026-05-14

### Opraveno
- Finální sjednocení threshold entit: 24h threshold je nyní pouze `number.hunter_irrigation_rain_threshold_24h`.
- Zachována finální 48h threshold entita `number.hunter_irrigation_rain_threshold_48h`.
- Doplňena a sjednocena migrace historických ID (`prah_srazek_24_h`, staré `rain_threshold`) na `rain_threshold_24h`.
- Dashboard modern verze používá pouze finální EN entity pro limity srážek.

### Přidáno
- Nativní runtime přepínač `switch.hunter_irrigation_manual_rain_block` přímo v integraci (bez externího helperu).
- Lokalizace názvu `manual_rain_block` v `cs` i `en` překladech.

### Změněno
- Dokumentace byla sjednocena na finální entity ID (EN) pro thresholdy i ruční blokaci deště.

## [1.0.21] - 2025-05-14

### Opraveno (KRITICKÉ)
- **Async blocking call VYŘEŠEN**: Místo `history.async_get_significant_states()` (neexistuje) používáme `hass.async_add_executor_job()` pro sync API
- Executor běží sync API v thread poolu → event loop není blokován
- To je standardní Home Assistant pattern
- Rain stats by měly být dostupné bez warning logů

### Vylepšeno
- Entity migration: lepší logování s [SETUP] prefixem
- Delete stará entita když nová existuje (čistší přístup)
- Oprava mapování `number.hunter_irrigation_prah_srazek_24_h` → EN `rain_threshold`

## [1.0.20] - 2025-05-14

### Opraveno (KRITICKÉ)
- **Blocking call error VYŘEŠEN**: Změnit z `history.get_significant_states()` (synchronní) na `history.async_get_significant_states()` (async)
- Předchozí verze způsobovala "RuntimeError: Caught blocking call" v logu
- Rain stats by nyní měly načítaní BEZ chyb
- Logování zůstává podrobné ([RAIN DATA] tagy) pro diagnózu

### Přidáno
- `input_boolean.hunter_irrigation_manual_rain_block` v dashboard example

## [1.0.19] - 2025-05-14

### Opraveno (KRITICKÉ)
- **Rain stats KONEČNĚ plnění daty**: Coordinator se nyní inicializuje hned při startu (nie v background). Srážkové sensory by měly vracet reálná čísla místo Unknown/None.
- **Interval srážek**: Snížen na 1 minutu pro debugging. Po ověření že funguje, změnit na 60 minut v sensor.py.
- **Entity registry migration**: Přesunuta DŘÍVE (PŘED platform setup), aby se staré CZ ID mapovaly správně na nové EN ID. `number.hunter_irrigation_rain_threshold` teď funguje.
- **Podrobné logování**: Všechny kroky mají tagy [RAIN], [RAIN DATA], [BLOCK], [UNBLOCK], [MANUAL] pro snadnou diagnózu.

### Přidáno
- **Suspend/Resume venilů**: Když je blokace aktivní → `switch.travnik_X_automatic_watering = OFF` (suspenduje plán v jednotce). Po odblokování → `ON` (obnoví plán).
- **Manual rain block helper**: `input_boolean.hunter_irrigation_manual_rain_block` - vytvořen automaticky. Použij pro testování blokace bez fyzických srážek.
- **Event listener**: Sleduje změny manual_rain_block a okamžitě aktualizuje runtime stav.

## [1.0.18] - 2025-05-13

Reverted (nebyly aplikovány správně)

## [1.0.17] - 2025-05-13

### Opraveno
- Stabilizováno načítání Recorder historie pro srážkové souhrny (`včera`, `předevčírem`, `24 h`, `48 h`, `7 dní`) přes kompatibilní volání API napříč verzemi Home Assistant.
- Sjednoceny interní entity ID na anglické názvy.
- Přidána migrace historických lokalizovaných entity ID (CZ) na anglické entity ID.

### Změněno
- Dashboard example znovu používá anglické interní entity ID a pouze viditelné názvy nechává v češtině.

## [1.0.16] - 2026-05-13

### Opraveno
- Dashboard example používá reálné české entity (`rain_guard_stav`, `rain_guard_duvod`, `srazky_za_poslednich_24_hodin`, `srazky_za_poslednich_48_hodin`, `prah_srazek_24_h`, `prah_srazek_48_h`).
- Výpočet srážek je kompatibilní s async i sync variantou Recorder API (`history.get_significant_states`), takže senzory už nepadají do `Neznámý`.
- Rain guard vrací plně české stavy a důvody blokace (např. `blokovano: srazky za 24 hodin`).
- Rain guard logika umí číst limity 24 h / 48 h i z lokalizovaných entity ID, takže funguje po update bez ručního mapování.

## [1.0.15] - 2026-05-13

### Přidáno
- Samostatný konfigurovatelný práh srážek za 48 hodin (`number.hunter_irrigation_rain_threshold_48h`).

### Změněno
- Rain guard nyní používá oba runtime prahy:
	- 24 h threshold (nastavitelný),
	- 48 h threshold (nastavitelný).
- Popisky v config flow, options flow a dashboardu jsou rozdělené na 24 h a 48 h.

### Opraveno
- Senzory srážek vrací `0.0` místo `unknown`, pokud v daném okně nejsou změny.
- Dashboard obsahuje obě threshold entity (24 h / 48 h).

## [1.0.14] - 2026-05-13

### Přidáno
- Nové senzory: `rain_last_24_hours_total` a `rain_last_48_hours_total` pro rolling okna srážek.
- Nové stavové senzory pro dashboard: `rain_guard_status` a `rain_guard_reason`.

### Změněno
- Rain guard logika je nyní primárně podle rolling oken:
	- nezavlažovat, pokud srážky za posledních 24 hodin >= threshold (výchozí 10 mm),
	- nezavlažovat, pokud srážky za posledních 48 hodin >= 25 mm.
- Threshold v UI je přejmenován na práh za posledních 24 h.
- Dashboard je zjednodušen a používá nativní rain guard status/reason místo šablonového textu.

### Opraveno
- Release workflow už negeneruje duplicitní verzi v titulku a těle release poznámek.

## [1.0.12] - 2026-05-13

### Opraveno
- Release nadpis je zkrácen na formát `[verze] - datum` bez duplicitního názvu integrace.
- Dashboard example doplněn o nativní Gardena plán (`next_cycle`) a auto/manual přepínače zón.

## [1.0.11] - 2026-05-13

### Opraveno
- Opraven výpočet rain souhrnů (včera, předevčírem, posledních 7 dní).
- Dashboard example upraven podle reálně dostupných entit a služeb.
- Release poznámky už neobsahují duplicitní nadpis verze v těle textu.

## [1.0.10] - 2026-05-13

### Opraveno
- Doplněna `after_dependencies: ["recorder"]` kvůli validaci Hassfest při použití `homeassistant.components.recorder`.

## [1.0.9] - 2026-05-13

### Přidáno
- Nové senzory srážek pro dashboard přehled: včera, předevčírem a součet za posledních 7 dní.

### Změněno
- Lokalizované názvy entit přes překlady (čeština/angličtina podle jazyka Home Assistantu).
- Dashboard example přepsán do formátu `sections`, aby šel vložit do aktuálního Raw editoru pohledu.

## [1.0.8] - 2026-05-13

### Opraveno
- Entity integrace jsou navazane na jedno zarizeni, takze detail v Home Assistantu je sjednoceny jako u beznych integraci.
- Dashboard example byl upraven pro aktualni entity a service volani (`zone_entity`) tak, aby se po vlozeni korektne zobrazil.

## [1.0.7] - 2026-05-13

### Opraveno
- Spravna HACS instalace: content_in_root false pro validaci repozitare + soubory prime v koreni ZIPu pro extrakci bez zdvojene slozky.


## [1.0.6] - 2026-05-13

### Opraveno
- Vrácen `content_in_root: false` pro správnou HACS validaci.

## [1.0.5] - 2026-05-13

### Opraveno
- Oprava HACS instalace: dvojitá složka (`hunter_irrigation/hunter_irrigation/`) odstraněna změnou `content_in_root: true`.

## [1.0.4] - 2026-05-13

### Opraveno
- Oprava struktury ZIP archivu pro správnou instalaci přes HACS.

## [1.0.3] - 2026-05-13

### Přidáno
- Konfigurační průvodce (UI `config_flow`) pro nastavení integrace bez úprav `configuration.yaml`.
- Options flow pro pozdější úpravu počtu zón, ventilů a dešťových senzorů přímo z UI Home Assistantu.
- Lokalizace průvodce (`strings.json`, `translations/cs.json`, `translations/en.json`).

### Změněno
- Integrace nyní běží přes `config entry` (`async_setup_entry`) místo YAML-only konfigurace.
- Platformy `number` a `switch` byly upraveny na setup přes config entry.
- Příklady konfigurace a dashboardu byly synchronizovány s reálnými entitami instalace.

## [1.0.2] - 2026-05-13

### Opraveno
- Opraven soubor `hacs.json` podle aktuálního schématu HACS (odstraněn nepodporovaný klíč `domains`).
- Doplněn klíč `issue_tracker` do integračního manifestu.
- Přidány lokální brand assets v cestě `custom_components/hunter_irrigation/brand/`.
- Odstraněn nepodporovaný klíč `homeassistant` z integračního manifestu kvůli Hassfest validaci.
- Přepnuto na release režim HACS (`zip_release` + `filename`), aby se v HA zobrazovala čísla verzí místo hashů commitů.
- Release workflow nyní publikuje pouze sekci konkrétní verze z `CHANGELOG.md`.
- Aktualizovány brand obrázky (`icon.png`, `logo.png`) na vlastní grafiku integrace.

## [1.0.1] - 2026-05-13

### Přidáno
- Vestavěné entity `number` pro délky zón a práh deště.
- Vestavěné entity `switch` pro manuální override a simulační režim.
- Aktualizovaný dashboard příklad používající entity vlastněné integrací.
- Česká dokumentace a aktualizovaný setup postup.

### Změněno
- Vyhodnocení délky zóny nyní preferuje runtime hodnoty řízené vestavěnými entitami.
- Práh deště lze vyhodnotit z runtime hodnoty i bez externí helper entity.

## [1.0.0] - 2026-05-13

### Přidáno
- První vydání vlastní HACS integrace.
- Služby: `hunter_irrigation.start_zone`, `hunter_irrigation.stop_zone`, `hunter_irrigation.preview_zone`.
- Logika blokování zálivky podle deště (denní déšť, okamžité srážky, binární senzor deště).
- Zpětná kompatibilita události `irrigation.preview_start_request`.


