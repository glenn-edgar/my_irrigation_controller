# eto_py3 — evapotranspiration (ETO) weather

Fetches weather data from multiple sources and computes **ETO**
(reference evapotranspiration), a measure of crop water demand. The irrigation
scheduler uses ETO (together with rainfall) to scale watering durations so the
system waters more in hot/dry conditions and less after rain.

Driven by `../eto_py3.py` (and the `../eto.bsh` periodic loop).

## Weather sources

| Source | Module |
|--------|--------|
| **CIMIS** (California Irrigation Management Information System) | `cimis_handlers_py3.py`, `cimis_spatial_py3.py` |
| **MesoWest / Messo** | `messo_handlers_py3.py` |
| **Weather Underground** personal weather station | `wunderground_personal_weather_station_py3.py` |
| **Ambient Weather** personal weather station | `ambient_weather_personal_weather_station_py3.py` |

## Modules

| File | Role |
|------|------|
| `eto_init_py3.py` | Initialization and ETO accumulation tables. |
| `calculate_eto_py3.py` | ETO computation from collected weather data. |
| `cimis_handlers_py3.py` | CIMIS station/data retrieval. |
| `cimis_spatial_py3.py` | Spatial interpolation of CIMIS data. |
| `messo_handlers_py3.py` | MesoWest data retrieval. |
| `wunderground_personal_weather_station_py3.py` | Wunderground PWS API. |
| `ambient_weather_personal_weather_station_py3.py` | Ambient Weather API. |

## Configuration & secrets

- Source selection / site parameters: `../system_data_files/eto_site_setup.json`.
- Credentials (e.g. the CIMIS email/IMAP login, API keys) are loaded into the
  Redis password DB by the external `passwords.py` — see
  [`../../docs/CONFIGURATION.md`](../../docs/CONFIGURATION.md).

Results (daily ETO, accumulation, rainfall history) are written to Redis and
consumed by the irrigation engine's `eto_management_py3.py` and shown on the
dashboard's ETO Management page.
