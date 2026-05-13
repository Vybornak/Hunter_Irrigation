# Seznam změn

V tomto souboru jsou evidovány všechny důležité změny projektu.

Formát vychází z Keep a Changelog a Semantic Versioning.

## [Nevydáno]

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


