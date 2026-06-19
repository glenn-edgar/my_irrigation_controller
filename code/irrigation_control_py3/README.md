# irrigation_control_py3 — irrigation engine

The core irrigation orchestration logic. It runs as a set of cooperating
**Chain Flow** chains (see [`../py_cf_new_py3/README.md`](../py_cf_new_py3/README.md))
that pop jobs from Redis queues, sequence valves safely, monitor flow/current,
and log every action. Started via `../irrigation_ctrl_startup_py3.py`.

## Responsibilities

- Process scheduled and operator-initiated irrigation jobs in order.
- Sequence valves safely: master valve → zone valve → monitor → close.
- Enforce flow and current limits; abort and report on anomalies.
- Manage filter cleaning / backwash.
- Apply ETO-based adjustment to watering durations.
- Record actions and failures to Redis streams for the dashboard.

## Modules

| File | Role |
|------|------|
| `irrigation_control_basic_py3.py` | Foundational control primitives shared across chains. |
| `common_irrigation_chains_py3.py` | Reusable Chain Flow chain definitions. |
| `irrigation_queue_processing_py3.py` | Pops jobs from the irrigation queues and drives execution. |
| `irrigation_step_monitoring_py3.py` | Monitors an in-progress step (duration, flow, current). |
| `master_valve_control_py3.py` | Master (main supply) valve state machine and safety. |
| `cleaning_valve_control_py3.py` | Filter cleaning / backwash valve control. |
| `clean_filter_py3.py` | Filter-cleaning operation. |
| `check_off_py3.py` | Verifies valves are off / closed (safety check). |
| `valve_resistance_check_py3.py` | Diagnostics on valve solenoid resistance. |
| `misc_support_py3.py` | I/O helpers for solenoids / equipment. |
| `Incomming_Queue_Management_py3.py` | Accepts external control commands into the queue. |
| `eto_management_py3.py` | Integrates ETO water-demand into scheduling. |
| `irrigation_logging_py3.py` | Logs actions/events to history streams. |
| `Failure_Report_py3.py` | Detects anomalies and emits failure reports. |

## Data flow

Jobs arrive on Redis job queues (enqueued by schedules in
`../app_data_files/` or by the web UI). The engine validates each job against
limits from `../system_data_files/` (e.g. `master_valve_setup.json`,
`valve_group_assignments.json`), actuates valves by issuing Modbus RPC calls to
the Modbus bridge, samples sensors, and appends history/error records to Redis
streams. See [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) for the
end-to-end cycle.
