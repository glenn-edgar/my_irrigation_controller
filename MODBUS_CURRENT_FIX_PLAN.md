# Modbus current-spike + sand-fouled-meter — fix plan

**Apply: 2026-06-20, AFTER the nightly irrigation cycle completes. NOT during an active cycle.**
Scoped 2026-06-19 from live evidence. Three independent root causes; do them in order.

## Evidence (why)
1. **Irrigation-current garbage spikes** — frequent. TIME_HISTORY 4:9 runs carry single +0.20 A samples (~20σ vs sd≈0.01); 74 stream outliers / 26h. Max ~1.31 A (< IRR_KILL 1.8 A).
2. **Equipment-current garbage spike** — rare but dangerous. 06-17 18:06:02 `plc_slave_1`=**1.255 A** (flat irrigation, steady 8.5 GPM = garbage, not load) **crossed EQ_KILL=1.2 A**. Did not trip KB1 (lucky timing). 1 in ~51h.
3. **Well flow meter sand-fouled** — *physical, not the desync*. On `No_city_water` runs `main_flow_meter`=flat 0.00 while Hunter holds 6–7 GPM (29/30 samples, 06-19 ~20:00). Well healthy; meter fouled.

Root cause of (1)+(2): unflushed Modbus serial buffer → self-sustaining frame desync (clears only on port reopen / reboot — last reboot 06-19 18:16). Garbage reaches the log because the relay returns CRC-failing frames, the client disables CRC, and the per-minute current log has no outlier filter.

## Safety / timing
- Apply only after the nightly cycle finishes (no active actuation).
- The `modbus_redis_server` (myModbus/rs485) is a long-running process — **restart it** to pick up A1–A3 (Werkzeug auto-reload only covers the Flask web procs, not this).
- Test reads on a throwaway / non-actuating path before trusting CRC changes (Safety Rule 4).
- One armed instance only; keep the bench/WSL instance stopped.
- Each edit is independent — revert the single line + restart to roll back.

---

## Part A — Controller (Python): stop the garbage frames
Repo (running): `nano_data_center/code/...` on `ssh pi@irrigation`. Order = lowest risk first.

### A1. Flush input buffer  — PRIMARY, lowest risk
`modbus_redis_server_py3/myModbus_py3.py:1033`, in `_communicate`, right after `self.serial.open()`:
```python
-        #self.serial.flushInput() TODO
+        self.serial.reset_input_buffer()      # pySerial 3.x; clears leftover bytes -> stops self-sustaining desync
```
Effect: a transient glitch re-syncs on the next transaction instead of needing a reboot. Risk: minimal.

### A2. Stop returning CRC-failing frames
`modbus_redis_server_py3/rs485_mgr_py3.py:74-75`, end of `process_message` (after the 5-retry loop):
```python
       total_failures =1
-       return total_failures , retries , response
+       return total_failures , retries , b""      # failed all retries -> hand back EMPTY, never the bad frame
```
`total_failures=1` already signals failure; an empty response makes any downstream `len(<4)` check reject it. Risk: low — confirm no caller consumes `response` while ignoring `total_failures`.

### A3. Re-enable client-side CRC on the read path  — the real fix
`plc_control_py3/new_instrument_py3.py` hardcodes `crc_flag = 0` at **131 (read_bits), 189, 214 (read_registers), 278, 315 (read_floats)**. `read_floats` (315) is the current-measurement path. Replace the disabled check with a real one, returning the raw response to `check_crc`:
```python
# read_floats (~308-318) — currently strips [2:] then sets crc_flag=0
-        return_data = self._communicate(message)
-        return_data = return_data[2:]
-        #crc_flag, return_data = self.check_crc( response )
-        crc_flag = 0
-        if crc_flag == 0:
-            return self._bytestringToFloat(return_data[1:], register_number)
+        response = self._communicate(message)
+        crc_flag, return_data = self.check_crc(response)   # validate full frame
+        if crc_flag != 0:
+            return None                                    # bad frame -> caller skips/repeats
+        return self._bytestringToFloat(return_data[1:], register_number)
```
**CAVEAT (test first):** reconcile `check_crc`'s `return_data` offset against the current `return_data[2:][1:]` slicing — a good frame must decode to the SAME value before/after. Validate on a throwaway read, then apply the same pattern to read_registers (214) and read_bits (131). **Callers must handle `None`** — check `measure_analog` / `make_current_measurement` skip or repeat on None. This is what actually stops a garbage frame from ever reaching KB1. Risk: medium (changes the read path for all PLC reads).

### A4. Outlier backstop on the logged current
`plc_io_cntrl_py3.py:67-87`, `make_current_measurement` — currently a single raw read → `-2.52` → `/.185` → `hset`, no filter. Add a **median-of-3 per channel** (mirror the existing `FILTERED_HUNTER` `filter_queue` at 115-118):
```python
# keep per-channel rings (e.g. self.irr_q / self.eq_q seeded [0,0,0]) and log the MEDIAN, not the raw sample
```
**Use median, NOT a clamp:** a clamp would also mask a *real* sustained overcurrent that KB1 must catch. Median-of-3 rejects a single garbage sample but passes a sustained (≥2 consecutive) real overcurrent. **CAVEAT:** confirm whether KB1's kill reads this per-minute logged value or a faster stream channel; if faster, the filter must live where KB1 reads. Risk: medium (must not blunt real overcurrent).

---

## Part B — Robot (Lua): sand-fouled-meter guard
Repo: `robot_operator/fleet_operations/irrigation_analytics` — `lib/well_drawdown.lua`, `chains/kb3_sustained_user_functions.lua`, `lib/controller_client.lua` (reads `main_flow_meter` + Hunter from controller redis). **Separate deploy** from Part A: this is the `irrigation-analytics` CONTAINER → needs image rebuild + push + redeploy (Part A only needs the modbus server restarted).

Add a guard: when `main_flow_meter (PLC well) ≈ 0` while `FILTERED_HUNTER > ~4 GPM`, sustained N samples, during a `No_city_water` (well) step →
- set `well_meter_fouled` flag,
- **suppress** PLC-based verdicts while flagged: well-drawdown (input is dead → blind) and internal-leak (`PLC≫HUNTER` inverts to `PLC≪HUNTER` → would mask 4:9 etc.),
- use **Filtered Hunter** as the flow reference for well runs while flagged,
- emit a once/day "clean the well flow meter" notice.

**Monitor-first (Safety Rule 5):** log `[monitor] WOULD suppress ...` first, validate against the currently-known fouled state, then arm. The pending KB3 leak-curve detector (NEXT BUILD) must key off Hunter for well runs anyway.

---

## Verify (over the cycle after applying)
- Re-scan TIME_HISTORY `*_CURRENT` arrays + `PLC_MEASUREMENTS_STREAM`: irr/equip `max` should track `mean` (no +0.2 outliers); equipment must never cross EQ_KILL 1.2 A.
- NOTE: the 18:16 reboot already re-aligned framing, so "no spikes" alone won't prove A1 — confirm the flush line actually executes (trace/log).
- Part B: confirm `[monitor] WOULD` fires on the fouled meter before arming suppression.

## Physical (operator)
- Clean the sand out of the well flow meter. Well is healthy (Hunter shows steady 6–7 GPM delivered).
