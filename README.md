# my_irrigation_controller

A Raspberry-Pi–based **IoT irrigation gateway** for an agricultural site
(deployment name **LaCima**). Originally developed as the "nano data center"
project for an IoT meetup, it orchestrates agricultural irrigation across a
distributed network of PLC controllers, wireless sensors, and cloud services.

**Redis is the central hub** for all runtime state, job queues, and a
configuration *graph*. A custom **Chain Flow** engine executes irrigation
sequences as event-driven state machines. The system bridges field hardware
(ESP32 / Click / PSoC PLCs over **Modbus/RS-485**, plus **MQTT** WiFi sensors)
into Redis, serves a **Flask** web dashboard, pulls **ETO** (evapotranspiration)
weather data to scale watering, and optionally writes an audit trail to
**Ethereum** while exchanging jobs with the cloud over **RabbitMQ**.

---

## Architecture at a glance

```
   Field sensors / valves                      Operator
   (Modbus RS-485, MQTT WiFi)                  (browser)
            │                                      │
            ▼                                      ▼
   ┌───────────────────┐                  ┌──────────────────┐
   │ modbus_server     │                  │ bootstrap_web    │  Flask + HTTPS
   │ mqtt_redis_gateway│                  │ (dashboard/UI)   │  Digest auth
   └────────┬──────────┘                  └────────┬─────────┘
            │                                      │
            ▼                                      ▼
   ┌─────────────────────────────────────────────────────────┐
   │                        REDIS                             │
   │  graph (db3) · io/files/tables (db4) · passwords (db5)   │
   │  mqtt (db6) · backup/mqtt (db7)                          │
   │  streams · job queues · state hashes · RPC channels      │
   └─────────────────────────────────────────────────────────┘
            ▲                    ▲                    ▲
            │                    │                    │
   ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐
   │ irrigation ctrl │  │ eto (weather)   │  │ monitoring      │
   │ (Chain Flow)    │  │ cloud / rabbitmq│  │ (pi, redis)     │
   └─────────────────┘  └─────────────────┘  └─────────────────┘
            │
            └──► critical events ──► Ethereum blockchain (optional audit log)
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full data-flow detail.

---

## Repository layout

| Path | Contents |
|------|----------|
| `code/` | All application code and entry points — [`code/README.md`](code/README.md) |
| `construct_graph_py3/` | Configuration-graph builder — [`construct_graph_py3/README.md`](construct_graph_py3/README.md) |
| `docs/` | Architecture, configuration, and deployment guides |
| `presentations/` | Original IoT-meetup slide decks (background material) |
| `redis/`, `redis-bak/` | A **vendored copy of upstream Redis** source — not part of this project's code (see note below) |

> **Note on `redis/` and `redis-bak/`:** these directories (~200 MB) are a
> bundled copy of the Redis database source with their own upstream README and
> license. They are not maintained here and are candidates for removal from the
> repository — install Redis from your OS package manager instead.

---

## Quick start

This system targets a Raspberry Pi (or similar Linux SBC) running a local Redis
server. Full instructions are in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

1. Install and start **Redis** locally (`127.0.0.1:6379`).
2. Create your secrets file from the template (see **Secrets** below).
3. Configure `code/system_data_files/redis_server.json`
   (copy from `redis_server_example.json`).
4. Build the configuration graph, then launch:

   ```bash
   cd code
   ./startup.bsh
   ```

   `startup.bsh` runs one-time initialization (loads passwords, files, and the
   system graph into Redis) and then starts the web server and process manager.

5. Open the dashboard at **`https://<host>`** (self-signed cert, HTTP Digest
   auth).

---

## Secrets

Secrets are **not** stored in this repository. A `passwords.py` script (kept
outside the repo, e.g. `/home/pi/passwords.py`) loads credentials into the
Redis *password* database (db 5) at startup. Use
[`code/passwords.template`](code/passwords.template) as the starting point — it
seeds keys for the CIMIS weather email, the RabbitMQ cloud gateway, MQTT, and
the Ethereum/ETO services. See [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md).

---

## Documentation map

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — data flow, Redis usage, comms
- [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) — config files, schedules, secrets
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — install, run, supervise
- [`code/README.md`](code/README.md) — entry points and launchers
- Subsystem READMEs under `code/*/` and `construct_graph_py3/`

---

## Status / caveats

- `code/requirements.txt` is pinned to a **2018-era** stack (Flask 0.12,
  Python 3.5–era packages). Treat it as a historical record; verify and update
  before deploying on current systems.
- Hard-coded paths in some `.bsh` scripts reference `/home/pi/nano_data_center`;
  adjust for the current install location (`~/my_irrigation_controller`).

## License

See [`LICENSE`](LICENSE).
