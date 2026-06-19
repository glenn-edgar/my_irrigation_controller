# Configuration

All configuration lives in two directories under `code/`, plus an external
secrets file. Most files are JSON; the configuration *graph* is built from these
and from the `construct_graph_py3/` modules.

## 1. System configuration — `code/system_data_files/`

Hardware wiring, Redis connection, and the built graph.

| File | Purpose |
|------|---------|
| `redis_server.json` | Redis host/port, logical DB numbers, site name, MQTT broker/topics. **Start here.** |
| `redis_server_example.json` | Template/example for the above. |
| `controller_pin_assignment.json` | GPIO/pin mapping for each PLC controller. |
| `controller_cable_assignment.json` | RS-485 serial port ↔ controller mapping (`.bak` is a backup). |
| `plc_inputs.json` | PLC analog/digital input definitions. |
| `master_valve_setup.json` | Master valve configuration (current/flow limits). |
| `master_valve_switches.json` | Master valve switch mappings. |
| `valve_group_assignments.json` | Valve groupings for coordinated control. |
| `global_sensors.json` | Sensor definitions (flow, current, moisture, etc.). |
| `eto_site_setup.json` | Weather data source configuration for ETO. |
| `extraction_file.pickle` | **Generated** — serialized configuration graph, loaded into Redis at startup. Rebuild with the graph builder, do not edit by hand. |

### `redis_server.json` keys

```jsonc
{
  "host": "127.0.0.1", "port": 6379,   // Redis instance
  "site": "LaCima",                     // logical site name
  "local_node": "nano_data_center",     // this processor's node name
  "graph_db": 3,                        // configuration graph
  "redis_io_db": 4, "redis_file_db": 4, // runtime io / loaded files
  "redis_table_db": 4, "mqtt_cloud_db": 4,
  "redis_password_db": 5,               // secrets (from passwords.py)
  "mqtt_db": 6,                         // local MQTT data
  "redis_backup_db": 7,                 // backup / overflow
  "mqtt_server": "nano_data_center_demo",
  "mqtt_topic": "REMOTES/#",
  "mqtt_upload_topic": "REMOTES/UPLOAD/LaCima",
  "mqtt_download_topic": "CLOUD/DOWNLOAD/LaCima",
  "mqtt_cloud_server": "lacimaRanch.cloudapp.net",
  "mqtt_cloud_port": 8883, "mqtt_port": 8883
}
```

> Known quirk: `mqtt_db` appears twice (6 and 7) in the shipped file — the last
> occurrence wins. Set the value you actually want and remove the duplicate.

## 2. Irrigation schedules — `code/app_data_files/`

Schedules and zone definitions consumed by the irrigation engine. `sprinkler_ctrl.json`
is the master index that references the individual schedule files.

| File | Purpose |
|------|---------|
| `sprinkler_ctrl.json` | Master schedule index (references the files below). |
| `city_avocado.json`, `city_rose.json`, `flowers.json`, `house.json` | Per-zone / per-crop schedules. |
| `left_bank.json`, `right_bank.json` | Zone-area schedules. |
| `Back_city_water.json`, `Back_no_city_water.json`, `No_city_water.json`, `no_city_water_back_up.json` | Variants for city-water vs. water-restricted periods. |
| `check_sprinkler.json`, `wait.json`, `test.json` | Diagnostic / test schedules. |
| `system_actions.json` | System-level action definitions. |
| `controller_*.json`, `eto_site_setup.json` | Copies of hardware/ETO config used at the app layer. |

## 3. Secrets — external `passwords.py` (NOT in the repo)

Secrets are never committed. At startup, an external script (e.g.
`/home/pi/passwords.py`) flushes the Redis *password* DB (db 5) and loads
credentials. Build it from [`../code/passwords.template`](../code/passwords.template).

Credentials seeded by the template include:

- `CIMIS_EMAIL` — IMAP username/password for fetching CIMIS weather data.
- `redis_gateway` — RabbitMQ cloud-gateway user/password/vhost/queue/port/server.
- Additional MQTT / Ethereum / ETO API keys as needed by your deployment.

The local MQTT broker and local web-server credentials are intentionally left in
place by the template (it does not overwrite them).

### Setup steps

1. Copy `code/passwords.template` to a location **outside** the repo, e.g.
   `/home/pi/passwords.py`.
2. Replace every `xxxx` placeholder with real credentials.
3. Confirm the path to `redis_server.json` near the top of the script matches
   your install location.
4. Ensure your startup script passes this path (the `.bsh` launchers reference
   `/home/pi/passwords.py`).

## Rebuilding the configuration graph

After changing any system config (controllers, sensors, packages), rebuild the
graph and reload it into Redis:

```bash
cd code
./reset_graph.bsh          # or: python3 -m redis_support_py3.construct_graph_py3
```

This regenerates `system_data_files/extraction_file.pickle` and repopulates the
graph DB. See [`../construct_graph_py3/README.md`](../construct_graph_py3/README.md).
