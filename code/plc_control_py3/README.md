# plc_control_py3 — PLC controller classes

Device-specific controller classes and a unified I/O abstraction for the
programmable logic controllers (PLCs) in the field. These models sit on top of
the Modbus bridge (see
[`../modbus_redis_server_py3/README.md`](../modbus_redis_server_py3/README.md))
and present a consistent I/O interface regardless of the underlying hardware.

## Supported controller types

- **ESP32** microcontrollers
- **Click** PLC boards
- **PSoC 4M** ARM-based controllers

These drive solenoid valves (master, cleaning, and zone valves) and read flow
meters, current sensors, and digital status inputs.

## Modules

| File | Role |
|------|------|
| `construct_classes_py3.py` | Factory that instantiates the right controller class per device (from the config graph). |
| `esp32_controller_class_py3.py` | ESP32 device interface. |
| `click_controller_class_py3.py` | Click PLC interface. |
| `psoc_4m_devices_py3.py` | PSoC 4M device interface. |
| `io_controller_py3.py` | Unified I/O abstraction over the controller classes. |
| `new_instrument_py3.py` | Instrument/measurement helper. |

## Related

- `../plc_io_cntrl_py3.py` periodically samples PLC measurements (flow/current)
  and writes them to Redis streams.
- Pin/cable mappings live in `../system_data_files/controller_pin_assignment.json`
  and `controller_cable_assignment.json`; input definitions in `plc_inputs.json`.
- Sensor definitions are in `../system_data_files/global_sensors.json`.
