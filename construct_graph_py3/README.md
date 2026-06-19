# construct_graph_py3 — configuration graph builder

This is the **offline configuration tool** that builds the system's
configuration *graph* — the single description of every site, processor,
package, data structure, controller, and field device, plus how they relate.
The graph is serialized to a pickle and loaded into Redis (graph DB, db 3) at
startup; the running code then *queries* the graph instead of hard-coding
addresses and wiring.

> Run this whenever you change hardware, sensors, schedules, or packages — then
> reload it into Redis. See [`../docs/CONFIGURATION.md`](../docs/CONFIGURATION.md).

## What the graph contains

- **Sites** — e.g. `CLOUD_SITE` (cloud servers/gateways) and `LaCima` (the local
  field deployment).
- **Processors** — nodes such as `nano_data_center`.
- **Packages** — collections of data structures per site (irrigation scheduling,
  MQTT devices, PLC devices, Redis monitoring, ETO management, etc.).
- **Data structures** — the streams, job queues, hashes, and RPC channels each
  package needs.
- **Controllers / devices** — PLC controllers, Modbus remote units, and their
  I/O links, addresses, and parameters.

## Top-level modules

| File | Role |
|------|------|
| `construct_graph_py3.py` | Main driver: assembles the whole system graph. |
| `build_configuration_py3.py` | Builds graph nodes, relationships, and properties. |
| `construct_data_structures_py3.py` | Defines the data structures (streams/queues/hashes) for packages. |

## `graph_modules_py3/`

Per-area and per-site builders:

| File | Role |
|------|------|
| `construct_applications_py3.py` | Defines applications (irrigation, ETO, monitoring). |
| `construct_controller_py3.py` | PLC controllers and their I/O links. |
| `construct_plc_devices_py3.py` | Modbus remote units / devices. |
| `construct_mqtt_devices_py3.py` | Wireless (MQTT) sensor network devices. |
| `construct_redis_monitor_py3.py` | Monitoring data streams. |
| `construct_cloud_interface_py3.py` | Cloud gateway configuration. |
| `plc_measurements_py3.py` | Flow/current sensor measurement definitions. |

Site-specific submodules live under `graph_modules_py3/lacima/`,
`.../cloud_site/`, and `.../application_modules_py3/` (e.g.
`construct_irrigation_scheduling_py3.py`, `construct_weather_stations_py3.py`).

## Output & loading

The builder produces `../code/system_data_files/extraction_file.pickle`. At
startup, `process_initialization_py3.py` (via
`redis_support_py3.construct_graph_py3`) loads it into the Redis graph DB. The
runtime query API is documented in
[`../code/redis_support_py3/README.md`](../code/redis_support_py3/README.md).

To rebuild: `cd ../code && ./reset_graph.bsh`.
