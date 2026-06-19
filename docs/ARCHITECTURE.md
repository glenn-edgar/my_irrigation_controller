# Architecture

This document describes how the irrigation controller's components fit together
and how they communicate. For per-subsystem detail, follow the links into the
`code/*/README.md` files.

## Design principles

1. **Redis is the single source of truth.** Every process reads and writes
   state, queues, and configuration through Redis rather than talking to each
   other directly. This decouples processes and makes the whole system
   inspectable from the web dashboard.
2. **Configuration is a graph.** The layout of sites, processors, packages,
   data structures, controllers, and devices is built once (offline) into a
   graph and loaded into Redis. Code then *queries* the graph at runtime instead
   of hard-coding wiring. See
   [`construct_graph_py3/README.md`](../construct_graph_py3/README.md).
3. **Behavior is expressed as Chain Flow.** Long-running, event-driven logic
   (especially irrigation sequencing and valve safety) is written as "chains"
   executed by a cooperative scheduler rather than as ad-hoc threads. See
   [`code/py_cf_new_py3/README.md`](../code/py_cf_new_py3/README.md).

## Process map

Processes are launched and supervised by the `.bsh` scripts and
`process_control_py3.py` (see [`code/README.md`](../code/README.md)). The main
long-running processes are:

| Process | Role |
|---------|------|
| `bootstrap_web_py3.py` | Flask web dashboard / control UI |
| `irrigation_ctrl_startup_py3.py` | Irrigation engine (Chain Flow) |
| `modbus_server_py3.py` | Modbus/RS-485 bridge, exposed via Redis RPC |
| `mqtt_redis_gateway_py3.py` | MQTT ↔ Redis bridge for WiFi sensors |
| `mqtt_scan_data_py3.py` | Sensor presence / reboot logger |
| `plc_io_cntrl_py3.py` | Periodic PLC measurement sampler |
| `eto_py3.py` | Evapotranspiration weather fetch / compute |
| `redis_monitoring_py3.py` | Redis server metrics → streams |
| `pi_monitoring_py3.py` | Host OS metrics → streams |
| `block_chain_input_handler_py3.py` | Optional Ethereum audit logger |
| `cloud_interface_py3.py` | Cloud job exchange via RabbitMQ |

## Redis database map

From `system_data_files/redis_server.json` (single Redis instance,
`127.0.0.1:6379`, multiple logical DBs):

| DB | Key in config | Purpose |
|----|---------------|---------|
| 3 | `graph_db` | Configuration graph (nodes, relationships, properties) |
| 4 | `redis_io_db`, `redis_file_db`, `redis_table_db`, `mqtt_cloud_db` | Runtime I/O data, loaded files, user tables, cloud MQTT cache |
| 5 | `redis_password_db` | Secrets loaded from the external `passwords.py` |
| 6 | `mqtt_db` | Local MQTT sensor data |
| 7 | `redis_backup_db` | Backup / overflow MQTT data |

> The JSON contains `mqtt_db` twice (6 and 7); the last value wins when parsed.
> This is a known quirk of the original config — verify the intended value for
> your deployment.

## Communication mechanisms

All inter-process communication flows through Redis using a small set of
patterns (built by `code/redis_support_py3/` — see its README):

- **Streams** — append-only time series: sensor readings, PLC measurements,
  irrigation action history, error logs, host/Redis metrics. The dashboard
  replays these for charts and history views.
- **Job queues (lists)** — pending vs. current irrigation jobs and individual
  valve operations. The irrigation engine pops jobs and processes them in order.
- **State hashes** — current values: master-valve state, suspend/enable flags,
  latest sensor readings, valve diagnostics.
- **RPC channels** — request/response over Redis. The Modbus bridge exposes a
  relay call so any process can perform Modbus I/O without owning the serial
  port. A generic RPC client/server pair is in `redis_support_py3/`.

External transports terminate at a bridge process and are normalized into the
Redis patterns above:

- **MQTT** — WiFi sensor network. Local broker topic `REMOTES/#`; cloud
  upload/download topics `REMOTES/UPLOAD/LaCima` and `CLOUD/DOWNLOAD/LaCima`
  (TLS port 8883). Bridged by `mqtt_redis_gateway_py3.py`.
- **Modbus / RS-485** — PLCs and remote I/O units. Bridged by
  `modbus_server_py3.py` + `code/modbus_redis_server_py3/`.
- **RabbitMQ** — cloud job exchange via `code/rabbitmq_support_py3/` and
  `cloud_interface_py3.py`.
- **Ethereum (Web3)** — optional immutable audit trail via
  `code/ethereum_block_chain/`.

## End-to-end: an irrigation cycle

1. A schedule (from `app_data_files/*.json`) or an operator action enqueues an
   irrigation job into a Redis job queue.
2. The irrigation engine (Chain Flow) pops the job, validates it against flow
   and current limits, and sequences the valves: open master → open zone →
   monitor → close zone → close master.
3. Valve actuation is performed by issuing Modbus RPC calls to the Modbus
   bridge, which drives the relay outputs on the field PLCs.
4. Flow/current sensors are sampled (`plc_io_cntrl_py3.py`, MQTT sensors) and
   written to Redis streams; a safety chain watches for over-current / over-flow
   and aborts if limits are exceeded.
5. Every action and any failure is appended to history streams and surfaced on
   the dashboard; critical events may also be written to the blockchain.
6. ETO weather data scales watering durations so the schedule adapts to recent
   evapotranspiration and rainfall.

## See also

- [`docs/CONFIGURATION.md`](CONFIGURATION.md) — every config file and schedule
- [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) — how to run and supervise the processes
