# py_cf_new_py3 — Chain Flow engine

**Chain Flow** is the project's custom, cooperative, event-driven execution
engine. Instead of threads or async frameworks, long-running behavior (most
importantly the irrigation sequencing and valve-safety logic) is expressed as
**chains**: ordered lists of operations that advance step by step in response to
events and conditions. A scheduler runs many chains together as a **cluster**.

Understanding this engine is the key to reading the irrigation control code.

## Concepts

- **Chain** — a named, ordered sequence of operations (think: a script / state
  machine). A chain has its own local state and advances one step per evaluation
  when its current step's condition is satisfied.
- **Opcode** — an individual operation a chain step performs (conditional, loop,
  call, wait/delay, send/receive event, etc.).
- **Event** — chains communicate by sending and waiting on named events, which
  lets one chain coordinate another (e.g. the irrigation chain signals the
  master-valve chain).
- **Cluster** — the collection of chains the scheduler cycles through; the main
  loop repeatedly gives each chain a chance to advance.
- **Dynamic chains** — chains can be created/modified at runtime.

## Modules

| File | Role |
|------|------|
| `chain_flow_py3.py` | Core interpreter: defines chains and executes them step by step. |
| `cluster_control_py3.py` | Manages and schedules multiple chains (the cluster). |
| `opcodes_py3.py` | The library of step operations available to chains. |
| `dynamic_chain_flow_py3.py` | Runtime creation/modification of chains. |
| `help_functions_py3.py` | Helpers for constructing chains. |
| `common_functions_py3.py` | Shared utilities used by the engine. |

## Typical usage

Higher-level code builds chains (e.g.
[`../irrigation_control_py3/common_irrigation_chains_py3.py`](../irrigation_control_py3/)),
registers them with a cluster, and then runs the scheduler's execute loop. Each
pass evaluates every chain's current step; steps that are waiting on an event or
delay simply do not advance until their condition is met. This yields
predictable, inspectable sequencing without preemptive concurrency.
