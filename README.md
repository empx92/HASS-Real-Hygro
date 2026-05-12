# Real Hygro (Luftentfeuchter)

Custom Home Assistant integration that creates a **dehumidifier** (`humidifier` platform) entity.

## Features

- Full UI setup via **Settings → Devices & Services** (Config Flow)
- Uses selected humidity sensor + selected switch
- Generic-humidifier-like control:
  - target humidity
  - wet/dry tolerance
  - min/max humidity range
- Minimum runtime protection (`hh:mm:ss`)
- Optional automatic mode:
  - if humidity rises by `x %` within `mm:ss`, turn on
  - runtime protection still applies

## Installation (HACS)

1. Open HACS → Integrations.
2. Add custom repository URL of this repository (category: Integration).
3. Install **Real Hygro**.
4. Restart Home Assistant.
5. Go to Settings → Devices & Services → Add Integration → **Real Hygro**.

## Notes

- The integration creates one humidifier-compatible entity with device class dehumidifier.
- Lovelace can control it with standard humidifier cards.
