# redis_support_py3 — Redis data layer

This package is the abstraction layer over Redis. Because Redis is the system's
central hub (see [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)),
almost every other subsystem builds its data structures, queries the
configuration graph, and makes RPC calls through here.

## What it provides

- **Data-structure factory** — typed wrappers over Redis primitives: streams
  (time series), job queues (lists), state hashes, and RPC channels — so callers
  work with "a job queue" or "a stream" rather than raw Redis commands.
- **Configuration graph** — builds and queries the graph of sites / processors /
  packages / data structures / controllers / devices that defines the system's
  wiring. Code queries this graph at runtime instead of hard-coding addresses.
- **Loaders** — load files and user data tables into Redis at startup.
- **RPC** — a generic request/response mechanism over Redis.
- **MQTT ingestion** — parse and store incoming MQTT sensor messages.

## Modules

| File | Role |
|------|------|
| `redis_constructs_py3.py` | Low-level wrappers over Redis hash/list/stream operations. |
| `construct_data_handlers_py3.py` | Factory that creates typed data handlers (stream, queue, hash, RPC) from the graph. |
| `construct_data_structures_py3.py` | Defines/instantiates the data structures for a package. |
| `construct_graph_py3.py` | Builds the configuration graph and loads it into the graph DB (db 3). |
| `graph_query_support_py3.py` | Query API over the graph (match by relationship/label/terminal). |
| `redis_stream_utilities_py3.py` | Helpers for time-series stream read/write/replay. |
| `redis_rpc_client_py3.py` / `redis_rpc_server_py3.py` | Generic RPC over Redis. |
| `load_files_py3.py` | Loads configuration/data files into Redis. |
| `user_data_tables_py3.py` | Loads user data tables into Redis. |
| `mqtt_client_py3.py` | MQTT client helper. |
| `mqtt_to_redis_py3.py` / `mqtt_message_processing_py3.py` | Ingest and parse MQTT messages into Redis. |
| `cloud_handlers_py3.py` | Cloud-side data handlers. |

## Graph query example (conceptual)

The graph-query API matches paths through the configuration graph, e.g. locate a
site's master valves:

```python
qs = Query_Support(...)
q = qs.add_match_relationship("SITE", "LaCima")
q = qs.add_match_terminal("MASTER_VALVES", "MASTER_VALVES")
results = qs.match_list(q)
```

The graph itself is built offline by the top-level
[`../../construct_graph_py3/`](../../construct_graph_py3/README.md) modules and
serialized to `system_data_files/extraction_file.pickle`, then loaded here.
