# modbus_redis_server_py3 — Modbus / RS-485 bridge

Bridges the field hardware (PLCs and remote I/O units on **Modbus over RS-485**,
with UDP/TCP variants) to the rest of the system via Redis. The bridge process
`../modbus_server_py3.py` owns the serial port(s) and exposes Modbus I/O as a
**Redis RPC** service, so any process can read sensors or actuate valves without
touching the hardware directly.

## Responsibilities

- Own and manage the RS-485 serial link(s) to the PLCs / remote units.
- Encode/decode Modbus messages, with retry and error handling.
- Expose a Modbus relay call over Redis RPC (request → response).
- Mirror I/O state into Redis and track communication statistics.

## Modules

| File | Role |
|------|------|
| `myModbus_py3.py` | Low-level Modbus protocol implementation. |
| `msg_manager_py3.py` | Modbus message formatting, sequencing, and retry logic. |
| `modbus_serial_ctrl_py3.py` | Serial (RS-485) transport control. |
| `rs485_mgr_py3.py` | RS-485 port/line management. |
| `modbus_tcp_control_py3.py` | Modbus over TCP transport. |
| `python_udp_server_py3.py` | UDP network interface for remote devices. |
| `modbus_redis_mgr_py3.py` | Bridges Modbus I/O ↔ Redis storage / RPC. |
| `modbus_statistics_py3.py` | Tracks message counts, success rates, and timing. |

## Configuration

Serial port ↔ controller mapping comes from
`../system_data_files/controller_cable_assignment.json`; device/remote-unit
addresses and parameters come from the configuration graph (see
[`../redis_support_py3/README.md`](../redis_support_py3/README.md)). Modbus
statistics are surfaced in the dashboard's Modbus Statistics page.

See also the PLC controller classes in
[`../plc_control_py3/README.md`](../plc_control_py3/README.md), which model the
specific device types reached over this bridge.
