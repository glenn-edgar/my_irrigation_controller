# Deployment & Operations

This system is designed to run on a Raspberry Pi (or similar Linux SBC) at an
irrigation site, with a local Redis server and serial (RS-485) + WiFi (MQTT)
links to field hardware.

## Prerequisites

- Linux host (originally Raspberry Pi OS).
- **Redis** server running locally on `127.0.0.1:6379`.
- **Python 3** with the project dependencies (see `code/requirements.txt`).
  > The pinned versions date from ~2018 (Flask 0.12, Python 3.5-era). Verify and
  > update them for current systems before relying on them.
- A local **MQTT broker** (e.g. Mosquitto) if using the WiFi sensor network.
- USB-to-RS-485 adapter(s) for the Modbus/PLC links.
- Optional: RabbitMQ (cloud exchange) and an Ethereum endpoint (audit log).

## Install

```bash
# 1. Get the code
cd ~/my_irrigation_controller/code

# 2. Install Python dependencies (review requirements.txt first)
pip3 install -r requirements.txt

# 3. Configure Redis connection / site
cp system_data_files/redis_server_example.json system_data_files/redis_server.json
#   edit redis_server.json for your host, site, DB numbers, MQTT broker

# 4. Create the secrets file OUTSIDE the repo (see docs/CONFIGURATION.md)
cp passwords.template /home/pi/passwords.py
#   edit /home/pi/passwords.py, replace all xxxx placeholders
```

## One-time initialization

Before the first run (and after any config-graph change), the system loads
passwords, files, user tables, and the configuration graph into Redis. This is
done by `process_initialization_py3.py`, which the startup scripts invoke:

```bash
cd code
python3 process_initialization_py3.py /home/pi/passwords.py \
    "-m redis_support_py3.construct_graph_py3" \
    "-m redis_support_py3.load_files_py3"
```

To rebuild just the graph later: `./reset_graph.bsh`.

## Running

The main launcher starts everything:

```bash
cd code
./startup.bsh
```

`startup.bsh` performs initialization, then launches:

- `./bootstrap_web_py3.bsh &` — the Flask web dashboard (restart loop).
- `./process_control_py3.bsh` — the process manager (restart loop), which spawns
  and supervises the worker processes (Modbus bridge, MQTT gateway, monitoring,
  irrigation engine, etc.).

### Launcher scripts (`code/*.bsh`)

| Script | Role |
|--------|------|
| `startup.bsh` | Top-level startup: init + web + process manager. |
| `bootstrap_web_py3.bsh` | Restart loop for the web server. |
| `process_control_py3.bsh` / `process_control.bsh` | Restart loop for the process manager. |
| `irrigation_startup.bsh` | Alternate startup focused on the irrigation engine. |
| `eto.bsh` | Periodic ETO weather fetch loop. |
| `reset_graph.bsh` | Rebuild the configuration graph into Redis. |
| `rabbit_web_access.bsh` | RabbitMQ/cloud access helper. |
| `python_process.bsh`, `utilities.bsh`, `pip_capture.bsh` | Helper scripts. |

The `.bsh` restart loops are a lightweight supervisor: each crashes-and-restarts
its Python process after a short delay and captures stderr to `/tmp/*.err`.

> **Path caveat:** several `.bsh` scripts hard-code `/home/pi/nano_data_center`.
> Update these to your install path (`~/my_irrigation_controller`) or create a
> matching symlink before running.

## Accessing the dashboard

- URL: `https://<host>` (HTTPS with a self-signed certificate).
- Auth: HTTP Digest. Configure the credentials in Redis (password DB) /
  `passwords.py`; do not ship defaults to production.

From the dashboard you can control irrigation, edit schedules/parameters, start
and stop processes, inspect Redis, and view sensor/PLC/host metrics. See
[`../code/bootstrap_web_py3/README.md`](../code/bootstrap_web_py3/README.md).

## Operating notes

- **Logs / errors:** worker stderr is written under `/tmp/*.err` by the restart
  loops; runtime events and history are in Redis streams (viewable in the UI).
- **Restarting a single service:** use the Process Control page in the dashboard
  rather than killing processes manually, so the supervisor stays consistent.
- **Recovering config:** if behavior looks wrong after editing JSON, rebuild the
  graph (`./reset_graph.bsh`) so Redis reflects your changes.

## Production hardening checklist

- [ ] Replace default web/MQTT credentials.
- [ ] Move `passwords.py` outside the repo and restrict its permissions.
- [ ] Update `requirements.txt` to maintained package versions.
- [ ] Fix hard-coded `/home/pi/nano_data_center` paths.
- [ ] Decide whether the vendored `redis/`, `redis-bak/` trees belong in the
      deployment (prefer an OS-packaged Redis).
