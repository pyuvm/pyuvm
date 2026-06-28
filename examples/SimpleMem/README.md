# SimpleMem — a worked example of a Custom UVM Agent

This example is the memory-bus complement to `examples/TinyALU/`. Where
TinyALU demonstrates the basic UVM phase loop, **SimpleMem** is written
to be a top-to-bottom reference for a standard A-to-Z UVM agent:

```
sequence_item  ->  sequence(s)  ->  sequencer  ->  driver  ->  DUT
                                                                |
                                                  monitor  <----+
                                                     |
                                            +--------+--------+
                                            v                 v
                                       scoreboard         coverage
```

The DUT is a tiny synchronous memory with a `req`/`gnt` handshake (see
`hdl/verilog/simple_mem.sv`). Everything else lives in
`testbench.py` so the file can be read in one pass.

## What this example shows that TinyALU does not

| Concept                                  | TinyALU         | SimpleMem               |
|------------------------------------------|-----------------|-------------------------|
| `uvm_sequence_item` + multiple sequences | ✓               | ✓                       |
| Driver / Monitor split                   | ✓ (siblings)    | ✓ (under a real agent)  |
| **`uvm_agent` with ACTIVE / PASSIVE**    | —               | ✓                       |
| `uvm_scoreboard` with golden model       | TLM-based       | golden-memory model     |
| `uvm_subscriber` coverage                | op coverage     | (op × addr-bucket) grid |
| **Negative test demonstrating coverage holes** | —         | ✓ (`expect_fail=True`)  |

## Tests

- `MemRandomTest` — random read/write traffic with the agent in ACTIVE
  mode. Exercises both the driver and the monitor.
- `MemWriteThenReadTest` — writes the full address space, then reads it
  back. The scoreboard's golden model must predict every read.
- `MemPassiveAgentTest` — switches the agent to **PASSIVE** via
  `ConfigDB().set(..., "is_active", UVM_PASSIVE)`. Stimulus is driven
  outside of UVM (a plain cocotb coroutine pokes the BFM). The monitor,
  scoreboard, and coverage subscriber must still cover the full
  (op, addr-bucket) grid.
- `MemPassiveFailingTest` — same passive setup but issues writes only.
  The coverage subscriber should flag the missing READ buckets and the
  test is marked `expect_fail=True` so `make` still exits 0.

## Running

```
cd examples/SimpleMem
make            # SIM=icarus by default
```

To use Verilator instead:

```
make SIM=verilator
```

Expected output ends with:

```
** TESTS=4 PASS=4 FAIL=0 SKIP=0
```
