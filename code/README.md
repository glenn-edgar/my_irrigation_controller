# code/ — application code

This directory contains all application code for the IoT irrigation gateway:
the entry-point processes, the `.bsh` launchers that supervise them, and the
subsystem packages. For the big picture see
[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

## Entry-point processes (`*_py3.py` at this level)

| Script | Role |
|--------|------|
| `process_initialization_py3.py` | One-time bootstrap: runs the passwords script, builds the config graph, loads files/tables into Redis. |
| `process_control_py3.py` | Process manager: spawns and supervises the worker processes below. |
| `bootstrap_web_py3.py` | Flask web dashboard / control UI. See [`bootstrap_web_py3/`](bootstrap_web_py3/README.md). |
| `irrigation_ctrl_startup_py3.py` | Irrigation engine startup (Chain Flow). See [`irrigation_control_py3/`](irrigation_control_py3/README.md). |
| `irrigation_int_py3.py` | Irrigation interface/integration entry (companion to the above). |
| `modbus_server_py3.py` | Modbus/RS-485 bridge, exposed via Redis RPC. See [`modbus_redis_server_py3/`](modbus_redis_server_py3/README.md). |
| `plc_io_cntrl_py3.py` | Periodic PLC measurement sampler (flow/current). See [`plc_control_py3/`](plc_control_py3/README.md). |
| `mqtt_redis_gateway_py3.py` | MQTT ↔ Redis bridge for the WiFi sensor network. |
| `mqtt_scan_data_py3.py` | Logs sensor presence / reboot / contact history. |
| `eto_py3.py` | Evapotranspiration weather fetch and compute. See [`eto_py3/`](eto_py3/README.md). |
| `redis_monitoring_py3.py` | Redis server metrics → streams. |
| `pi_monitoring_py3.py` | Host OS metrics (CPU/RAM/disk/temp) → streams. |
| `block_chain_input_handler_py3.py` | Optional Ethereum audit logger. See [`ethereum_block_chain/`](ethereum_block_chain/). |
| `cloud_interface_py3.py` | Cloud job exchange via RabbitMQ. See [`rabbitmq_support_py3/`](rabbitmq_support_py3/). |
| `utilities_py3.py` | Shared Linux/process/logging helpers. |

## Launchers (`*.bsh`)

`startup.bsh` is the top-level entry point; it runs initialization, then starts
the web server and process manager (each in its own crash-restart loop). See
[`../docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md) for the full list and the
hard-coded-path caveat.

## Subsystem packages

| Package | Responsibility |
|---------|----------------|
| [`irrigation_control_py3/`](irrigation_control_py3/README.md) | Irrigation orchestration, valve control, scheduling, failure reporting. |
| [`py_cf_new_py3/`](py_cf_new_py3/README.md) | **Chain Flow** — the event-driven execution engine. |
| [`redis_support_py3/`](redis_support_py3/README.md) | Redis data-structure factory, graph queries, RPC. |
| [`modbus_redis_server_py3/`](modbus_redis_server_py3/README.md) | Modbus protocol + RS-485 serial bridge to Redis. |
| [`plc_control_py3/`](plc_control_py3/README.md) | PLC controller classes (ESP32 / Click / PSoC) and I/O abstraction. |
| [`eto_py3/`](eto_py3/README.md) | Weather sources and ETO computation. |
| [`bootstrap_web_py3/`](bootstrap_web_py3/README.md) | Flask dashboard page/endpoint modules. |
| `mqtt_clients/` | MQTT publish/subscribe client helpers. |
| `rabbitmq_support_py3/` | RabbitMQ RPC client/server for the cloud. |
| `ethereum_block_chain/` | Web3 / smart-contract audit logging. |
| `web_support_py3/` | HTTP(S) client helpers for internal APIs. |
| `core_libraries/` | Common utilities (hash control, current monitor, topological sort). |
| `python_utilities_py3/` | General Python utilities. |
| `flask_web/`, `future_web/`, `future/`, `obsolete/` | Legacy / experimental / retired code (not part of the active path). |

## Config & data directories

| Directory | Contents |
|-----------|----------|
| `system_data_files/` | Hardware wiring, Redis config, generated graph pickle. See [`../docs/CONFIGURATION.md`](../docs/CONFIGURATION.md). |
| `app_data_files/` | Irrigation schedules and zone definitions. |

## Secrets

`passwords.template` is the template for the external `passwords.py` secrets
loader, which must live **outside** the repository. See
[`../docs/CONFIGURATION.md`](../docs/CONFIGURATION.md).
