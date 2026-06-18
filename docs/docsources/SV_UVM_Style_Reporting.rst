SV-UVM-Style Reporting
======================

pyuvm uses Python logging as its reporting backend. Existing testbenches can
continue to use ``self.logger.info()``, ``self.logger.warning()``, and
``self.logger.error()`` directly.

For testbenches that need UVM-style report IDs, UVM verbosity filtering,
severity counts, report summaries, or report catching, pyuvm also provides an
opt-in SV-UVM-style reporting path. The UVM-style layer performs the UVM
reporting decisions and then emits through Python logging.

Enabling SV-UVM-Style Reporting
-------------------------------

Enable the shared reporting mode before creating UVM objects or components:

.. code-block:: bash

   PYUVM_ENABLE_SV_UVM_STYLE_REPORTING=1 make sim

You can also enable it from Python before constructing the testbench:

.. code-block:: python

   from pyuvm import set_sv_uvm_style_reporting_enabled

   set_sv_uvm_style_reporting_enabled(True)

When this mode is enabled, ``uvm_object`` loggers propagate to the shared
``uvm`` logger. In this mode, ``uvm_report_object`` does not install a default
stream handler on every report object. This preserves Python logging as the
transport while giving the testbench a shared path for report rendering.

To collect severity counts, use report summaries, or install report catcher
rules, create the report server early in the test:

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

   import logging
   from pyuvm import uvm_report_server

   report_server = uvm_report_server.get()
   report_server.log_summary(logging.getLogger("uvm"))
   report_server.assert_no_failures("end of test")

By default, warnings do not fail the test, while errors and fatals do. The
policy can be changed when the report server is created:

.. code-block:: python

   from pyuvm import uvm_report_policy, uvm_report_server

   policy = uvm_report_policy(fail_on_warning=True, max_quit_count=5)
   uvm_report_server.create(policy=policy)

Report Catching
---------------

The report server supports simple severity rewrites by report ID and message
regular expression:

.. code-block:: python

   from pyuvm import UVM_WARNING, uvm_report_server

   report_server = uvm_report_server.get()
   report_server.add_change_sev("KNOWN_ISSUE", "temporary", UVM_WARNING)

   self.uvm_report.error("KNOWN_ISSUE", "temporary mismatch")

Formatter Relationship
----------------------

SV-UVM-style reporting does not replace Python logging. It provides UVM-shaped
report metadata and filtering before the message reaches logging. The rendered
timestamp, hierarchy, filename, line number, and final text layout still come
from the active Python logging formatter.

pyuvm's ``PyuvmFormatter`` remains the customization point for teams that want
a different log layout while keeping the UVM-style report metadata, verbosity
filtering, counts, summaries, and catcher behavior.
