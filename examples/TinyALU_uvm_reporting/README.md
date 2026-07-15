# TinyALU SV-UVM-Style Reporting Example

This example uses the same TinyALU RTL and BFM as `examples/TinyALU`, but it
demonstrates pyuvm's opt-in SV-UVM-style reporting path. The original TinyALU
example remains the direct Python logging walkthrough.

Run the full reporting regression:

```sh
make SIM=verilator TOPLEVEL_LANG=verilog sim checkclean
```

The regression runs:

- `AluTest`: passing ALU traffic with a report summary and `TEST_STATUS: PASSED`.
- `ParallelTest`: forked random and max-value sequences.
- `FibonacciTest`: sequence reporting through the sequence's own
  `self.uvm_report`.
- `AluTestErrors`: real scoreboard mismatches reported as UVM errors.
- `FatalReportTest`: the same mismatch path reported with
  `self.uvm_report.fatal()`, expected by cocotb as `RuntimeError`.
- `FatalDowngradeToErrorTest`: the fatal mismatch path with the scoreboard
  report ID downgraded to `UVM_ERROR`, including a `[SEVCHG]` diagnostic.
- `FatalDowngradeToInfoTest`: the fatal mismatch path downgraded to `UVM_INFO`.
- `ErrorDowngradeToInfoTest`: the error mismatch path downgraded to `UVM_INFO`.

Run one test by name:

```sh
COCOTB_TEST_FILTER=FatalDowngradeToErrorTest make SIM=verilator TOPLEVEL_LANG=verilog sim checkclean
```

Useful reporting controls can be passed as plusargs:

```sh
make SIM=verilator TOPLEVEL_LANG=verilog \
    COCOTB_PLUSARGS="+UVM_VERBOSITY=DEBUG +max_quit_count=25 +test_status_label=MY_TEST_STATUS +print_char_len=80" \
    sim checkclean
```

`+max_quit_count=0` means unlimited errors. The summary prints that limit as
`UNLIMITED`:

```text
INFO     ..orting/uvm_report_server.py(...) [uvm_test_top]: UVM_ERROR   :    8
INFO     ..orting/uvm_report_server.py(...) [uvm_test_top]: Quit count :     8 of UNLIMITED (UVM_ERROR)
INFO     ..orting/uvm_report_server.py(...) [uvm_test_top]: TEST_STATUS: FAILED
```

Run the quit-count demo at `0`, `1`, `2`, and `25`:

```sh
make SIM=verilator TOPLEVEL_LANG=verilog maxquit-demo
```

UVM-style records show the source file and line, UVM hierarchy, and report ID:

```text
CRITICAL .._uvm_reporting/testbench.py(278) [uvm_test_top.env.scoreboard]: [scoreboard] FAILED: ...
```

Direct Python logger records are still ordinary logging records; they are not
counted by the report server and are not rewritten as UVM reports.
