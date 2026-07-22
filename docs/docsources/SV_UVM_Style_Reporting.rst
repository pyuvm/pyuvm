SV-UVM-Style Reporting
======================

pyuvm uses Python logging as its reporting backend. Existing testbenches can
continue to use ``self.logger.info()``, ``self.logger.warning()``, and
``self.logger.error()`` directly.

For testbenches that need UVM-style report IDs, UVM verbosity filtering,
severity counts, report summaries, or report catching, pyuvm also provides an
opt-in SV-UVM-style reporting path. The UVM-style layer performs the UVM
reporting decisions and then emits through Python logging.

The runnable ``examples/TinyALU_uvm_reporting/testbench.py`` example shows this
flow in a complete TinyALU simulation, including report IDs, runtime verbosity,
source file and line formatting, severity counts, quit-count handling, fatal
reports, and a final report summary.

Enabling SV-UVM-Style Reporting
-------------------------------

Enable the shared reporting mode before creating UVM objects or components:

.. code-block:: bash

   PYUVM_ENABLE_SV_UVM_STYLE_REPORTING=1 make sim

In cocotb simulations, the same mode can be enabled with a plusarg:

.. code-block:: bash

   make sim COCOTB_PLUSARGS="+PYUVM_ENABLE_SV_UVM_STYLE_REPORTING=1"

You can also enable it from Python before constructing the testbench:

.. code-block:: python

   from pyuvm import set_sv_uvm_style_reporting_enabled

   set_sv_uvm_style_reporting_enabled(True)

When this mode is enabled, ``uvm_object`` loggers propagate to the shared
``uvm`` logger. In this mode, ``uvm_report_object`` does not install a default
stream handler on every report object. This preserves Python logging as the
transport while giving the testbench a shared path for report rendering.

When this mode is enabled, ``uvm_test`` creates the shared report server during
test construction. This gives every component and sequence a common server for
severity counts, summaries, quit-count handling, and report catcher rules
before build phase starts.

Runtime reporting options are resolved from cocotb plusargs first, then
environment variables, then defaults:

* ``UVM_VERBOSITY``
* ``UVM_FAIL_ON_WARNING``
* ``UVM_FAIL_ON_ERROR``
* ``UVM_FAIL_ON_FATAL``
* ``max_quit_count`` or ``UVM_MAX_QUIT_COUNT``
* ``test_status_label`` or ``TEST_STATUS_LABEL``
* ``print_char_len`` or ``UVM_PRINT_CHAR_LEN``

For objects that are not under a ``uvm_test``-managed simulation, the report
server can still be created explicitly:

.. code-block:: python

   from pyuvm import UVM_LOW, uvm_report_server

   report_server = uvm_report_server.create(verbosity=UVM_LOW)

Writing Reports
---------------

Every ``uvm_object`` has a ``uvm_report`` property. Use it when you want
UVM-style report IDs and UVM verbosity semantics:

.. code-block:: python

   from pyuvm import UVM_HIGH, UVM_LOW, uvm_component


   class Scoreboard(uvm_component):
       def check_phase(self):
           self.uvm_report.info("SCOREBOARD", "checking final results", UVM_LOW)

           if self.mismatch_seen:
               self.uvm_report.error("SCOREBOARD", "result mismatch detected")
           else:
               self.uvm_report.info("SCOREBOARD", "all results matched", UVM_HIGH)

The available report methods are:

* ``self.uvm_report.info(report_id, message, verbosity)``
* ``self.uvm_report.warning(report_id, message)``
* ``self.uvm_report.error(report_id, message)``
* ``self.uvm_report.fatal(report_id, message)``

UVM Verbosity
-------------

UVM verbosity is not mapped onto Python logging levels. It is evaluated before
the logging call using UVM semantics: an info report passes when its message
verbosity is less than or equal to the configured verbosity.

.. code-block:: python

   from pyuvm import UVM_HIGH, UVM_LOW, uvm_report_server

   uvm_report_server.create(verbosity=UVM_LOW)

   self.uvm_report.info("LOW_ID", "visible", UVM_LOW)
   self.uvm_report.info("HIGH_ID", "suppressed", UVM_HIGH)

Warning, error, and fatal reports are severity reports. They are not suppressed
by info verbosity. Python logging levels still carry severity to the backend
formatter and handlers.

Report Summary and Failure Policy
---------------------------------

The report server tracks UVM severity counts. At the end of a test, emit a
summary and assert the failure policy:

.. code-block:: python

   from pyuvm import uvm_report_server

   report_server = uvm_report_server.get()
   fail_msg = None
   try:
       report_server.log_summary(self.logger, self.get_full_name())
       fail_msg = report_server.log_final_status(
           self.logger,
           self.get_name(),
           uvm_full_name=self.get_full_name(),
       )
   finally:
       report_server.shutdown()

   if fail_msg is not None:
       raise AssertionError(fail_msg) from None

Call ``log_summary()`` and ``log_final_status()`` before ``shutdown()`` if you
want those lines to use the UVM-style source-location formatter. ``shutdown()``
restores the original Python logging formatters.

By default, warnings do not fail the test, while errors and fatals do. The
policy can be changed with runtime options, or when the report server is
created explicitly:

.. code-block:: python

   from pyuvm import uvm_report_policy, uvm_report_server

   policy = uvm_report_policy(
       fail_on_warning=True,
       max_quit_count=5,
       test_status_label="MY_TEST_STATUS",
   )
   uvm_report_server.create(policy=policy)

``log_final_status()`` emits ``TEST_STATUS: PASSED`` or
``TEST_STATUS: FAILED`` by default. Set ``test_status_label`` in the policy, or
pass ``test_status_label=...`` to ``log_final_status()``, when local automation
expects a different status token.

``max_quit_count`` controls how many UVM error reports are emitted before later
UVM error reports are suppressed. A value of ``0`` means unlimited: all UVM
errors are reported, no ``MAXQUIT`` warning is emitted, and the summary prints
``UNLIMITED`` as the limit.

.. code-block:: text

   INFO     ..orting/uvm_report_server.py(...) [uvm_test_top]: UVM_ERROR   :    8
   INFO     ..orting/uvm_report_server.py(...) [uvm_test_top]: Quit count :     8 of UNLIMITED (UVM_ERROR)
   INFO     ..orting/uvm_report_server.py(...) [uvm_test_top]: TEST_STATUS: FAILED

When the quit count is positive and reached, the triggering UVM error is logged,
then the report server emits a ``[MAXQUIT]`` warning. The summary and final
status are still printed so the simulation exits with a complete report.

.. code-block:: text

   ERROR    .._uvm_reporting/testbench.py(278) [uvm_test_top.env.scoreboard]: [scoreboard] FAILED: ...
   WARNING  .._uvm_reporting/testbench.py(278) [uvm_test_top.env.scoreboard]: [MAXQUIT] Quit count reached: 1 of 1 (UVM_ERROR)
   INFO     ..orting/uvm_report_server.py(...) [uvm_test_top]: UVM_ERROR   :    1
   INFO     ..orting/uvm_report_server.py(...) [uvm_test_top]: TEST_STATUS: FAILED

Report Catching
---------------

The report server supports simple severity rewrites by report ID and message
regular expression. Tests can install project- or test-specific demotions by
overriding ``add_message_demotes(self, catcher)``:

.. code-block:: python

   from pyuvm import UVM_WARNING, uvm_test

   class MyTest(uvm_test):
       def add_message_demotes(self, catcher):
           super().add_message_demotes(catcher)
           catcher.add_change_sev("KNOWN_ISSUE", "temporary", UVM_WARNING)

       def run_phase(self):
           self.uvm_report.error("KNOWN_ISSUE", "temporary mismatch")

A fatal report can also be downgraded before it is emitted. In that case it is
counted and logged at the downgraded severity and does not raise the
``RuntimeError`` used for an actual ``UVM_FATAL``:

.. code-block:: python

   from pyuvm import UVM_ERROR, uvm_test

   class MyTest(uvm_test):
       def add_message_demotes(self, catcher):
           super().add_message_demotes(catcher)
           catcher.add_change_sev("KNOWN_FATAL", "expected", UVM_ERROR)

       def run_phase(self):
           self.uvm_report.fatal("KNOWN_FATAL", "expected fatal condition")

When a catcher changes severity, the report server emits a UVM-style
``[SEVCHG]`` info record at the original report call site. This diagnostic is
not included in report severity counts.

Formatter Relationship
----------------------

SV-UVM-style reporting does not replace Python logging. It provides UVM-shaped
report metadata and filtering before the message reaches logging. The rendered
timestamp, hierarchy, filename, line number, and final text layout still come
from the active Python logging formatter.

Only UVM-style records emitted through ``self.uvm_report`` or
``uvm_report_server`` summary/status helpers are rewritten with UVM report
metadata. Direct Python logger records keep their normal logger name and are not
counted by the report server.

The default UVM-style wrapped formatter changes the rendered logger name for
UVM records to the source location, such as ``testbench.py(278)``, and prefixes
the message with the UVM full name and report ID:

.. code-block:: text

   CRITICAL .._uvm_reporting/testbench.py(278) [uvm_test_top.env.scoreboard]: [scoreboard] FAILED: ...

The ``stacklevel`` used by ``uvm_reporter`` preserves the user report call site
instead of pointing at the reporting helper. Summary and final-status records
intentionally point at ``uvm_report_server.py`` because those records originate
from the report server.

pyuvm's ``PyuvmFormatter`` remains the customization point for teams that want
a different log layout while keeping the UVM-style report metadata, verbosity
filtering, counts, summaries, and catcher behavior.

TinyALU Reporting Example
-------------------------

Run the complete TinyALU reporting regression with:

.. code-block:: bash

   cd examples/TinyALU_uvm_reporting
   make SIM=verilator TOPLEVEL_LANG=verilog sim checkclean

The regression includes:

* ``AluTest``: passing ALU traffic with summary and ``TEST_STATUS: PASSED``.
* ``ParallelTest``: forked random/max sequences.
* ``FibonacciTest``: sequence reporting through its own ``self.uvm_report``.
* ``AluTestErrors``: real scoreboard mismatches reported as UVM errors.
* ``FatalReportTest``: the same mismatch path reported through
  ``self.uvm_report.fatal()`` and expected by cocotb as ``RuntimeError``.
* ``FatalDowngradeToErrorTest``: the fatal mismatch path downgraded to
  ``UVM_ERROR`` so it exits through the normal summary/status failure path and
  shows a ``[SEVCHG]`` diagnostic.
* ``FatalDowngradeToInfoTest``: the fatal mismatch path downgraded to
  ``UVM_INFO`` so the waived mismatches pass through the final status check.
* ``ErrorDowngradeToInfoTest``: the error mismatch path downgraded to
  ``UVM_INFO`` with no UVM error count.

The example accepts reporting controls through plusargs or matching environment
variables:

.. code-block:: bash

   make SIM=verilator TOPLEVEL_LANG=verilog \
       COCOTB_PLUSARGS="+UVM_VERBOSITY=DEBUG +max_quit_count=25 +test_status_label=MY_TEST_STATUS +print_char_len=80" \
       sim checkclean

The ``maxquit-demo`` target runs the error test at ``0``, ``1``, ``2``, and
``25`` so the quit-count behavior is visible in one command:

.. code-block:: bash

   make SIM=verilator TOPLEVEL_LANG=verilog maxquit-demo
