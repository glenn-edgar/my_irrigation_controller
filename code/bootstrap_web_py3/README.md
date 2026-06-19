# bootstrap_web_py3 — web dashboard

The Flask web dashboard and control UI. The application is initialized by
`../bootstrap_web_py3.py` (served over HTTPS with HTTP Digest authentication);
each module here registers a section of pages and AJAX endpoints. All data is
read from and written to Redis, so the dashboard is effectively a live window
onto the system's central state.

## Capabilities

- **Irrigation control** — manually queue/cancel/prioritize jobs, edit schedule
  parameters, view the running and pending queue and past actions.
- **ETO management** — view weather data and adjust ETO settings.
- **Sensor / PLC streams** — live charts of MQTT sensors and PLC flow/current.
- **Management** — Redis inspection, MQTT device status, Modbus statistics,
  process start/stop, configuration file editing, host (Linux) metrics.

## Modules

| File | Section |
|------|---------|
| `load_static_pages_py3.py` | Static pages (login, navbar, dashboard shell). |
| `load_irrigation_control_py3.py` | Irrigation control + scheduling UI. |
| `load_irrigation_statistics.py` | Historical irrigation logs/charts. |
| `load_eto_management_py3.py` | ETO settings and weather display. |
| `load_mqtt_management_py3.py` | MQTT sensor device management. |
| `load_modbus_statistics_py3.py` | Modbus communication statistics. |
| `load_process_control_py3.py` | Start/stop/restart system processes. |
| `load_configuration_py3.py` | Configuration file editor. |
| `load_app_sys_files_py3.py` | App/system file upload/download. |
| `load_redis_management_py3.py` | Redis administration views. |
| `load_redis_access_py3.py` | Direct Redis key/hash/stream inspection. |
| `load_linux_management_py3.py` | Host OS monitoring (CPU/RAM/disk/temp). |
| `load_site_map_py3.py` | Site / location overview. |
| `base_stream_processing_py3.py` | Base class for live stream/chart views. |

## Access

- URL: `https://<host>` (self-signed certificate).
- Auth: HTTP Digest; credentials come from the Redis password DB. **Change the
  defaults before exposing the dashboard.**

Front-end assets (Bootstrap, JS, CSS) are bundled under `static/` in this
package. The companion `../web_support_py3/` provides the internal HTTPS client.
