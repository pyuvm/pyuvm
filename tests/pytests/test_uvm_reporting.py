import io
import logging
import uuid

import cocotb
import pytest

from pyuvm import (
    UVM_ERROR,
    UVM_FULL,
    UVM_HIGH,
    UVM_INFO,
    UVM_LOW,
    UVM_NONE,
    UVM_WARNING,
    get_sv_uvm_style_reporting_enabled,
    set_sv_uvm_style_reporting_enabled,
    uvm_component,
    uvm_report_object,
    uvm_report_policy,
    uvm_report_server,
    uvm_reporter,
    uvm_sequence,
    uvm_sequence_item,
    uvm_test,
    uvm_transaction,
)
from pyuvm._s13_uvm_component import uvm_test as internal_uvm_test


def _purge_uvm_logger_handlers():
    """Remove handlers leaked onto ``uvm`` child loggers by prior tests.

    ``uvm_report_object`` derives its logger name from ``id(self)`` (see
    ``get_initial_logger_name``), and Python caches loggers and their handlers
    globally forever. When CPython reuses a freed object's ``id()``, a later
    object can retrieve a cached logger still carrying handlers a previous test
    added via ``add_logging_handler`` and never removed. Clearing them between
    tests keeps these order-dependent leaks from crossing test boundaries.
    """
    manager = logging.root.manager
    for name, logger in list(manager.loggerDict.items()):
        if name == "uvm" or name.startswith("uvm."):
            if isinstance(logger, logging.Logger):
                for handler in list(logger.handlers):
                    logger.removeHandler(handler)


@pytest.fixture(autouse=True)
def clean_report_server():
    _purge_uvm_logger_handlers()
    set_sv_uvm_style_reporting_enabled(False)
    manager = uvm_report_server.get_or_none()
    if manager is not None:
        manager.shutdown()
        manager.clear_counts()
        manager.catcher.clear()
    yield
    set_sv_uvm_style_reporting_enabled(False)
    manager = uvm_report_server.get_or_none()
    if manager is not None:
        manager.shutdown()
        manager.clear_counts()
        manager.catcher.clear()
    _purge_uvm_logger_handlers()


@pytest.fixture()
def reporting_logger():
    created = []

    def make(
        verbosity=UVM_LOW,
        print_char_len=300,
        policy=None,
        fmt="%(levelname)s:%(message)s",
    ):
        name = f"uvm_reporting_test.{uuid.uuid4().hex}"
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)

        manager = uvm_report_server.create(
            root_logger=logger,
            verbosity=verbosity,
            policy=policy,
            print_char_len=print_char_len,
        )
        manager.register_logger(logger)
        created.append((logger, handler))
        return manager, logger, stream

    yield make

    for logger, handler in created:
        logger.removeHandler(handler)


@pytest.fixture()
def uvm_root_reporting():
    set_sv_uvm_style_reporting_enabled(True)
    logger = logging.getLogger("uvm")
    old_level = logger.level
    old_propagate = logger.propagate

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    manager = uvm_report_server.create(root_logger=logger, verbosity=UVM_LOW)
    manager.register_logger(logger)
    yield manager, stream

    manager.shutdown()
    logger.removeHandler(handler)
    logger.setLevel(old_level)
    logger.propagate = old_propagate


def test_info_obeys_verbosity(reporting_logger):
    manager, logger, stream = reporting_logger(verbosity=UVM_LOW)
    reporter = uvm_reporter(logger, UVM_LOW)

    reporter.info("LOW_ID", "visible info", UVM_LOW)
    reporter.info("HIGH_ID", "suppressed info", UVM_HIGH)

    output = stream.getvalue()
    assert "[LOW_ID] visible info" in output
    assert "suppressed info" not in output
    assert manager.get_stats().info_count == 1


def test_warning_error_and_fatal_ignore_info_verbosity(reporting_logger):
    manager, logger, stream = reporting_logger(verbosity=UVM_NONE)
    reporter = uvm_reporter(logger, UVM_NONE)

    reporter.warning("WARN_ID", "visible warning")
    reporter.error("ERR_ID", "visible error")
    with pytest.raises(RuntimeError):
        reporter.fatal("FATAL_ID", "visible fatal")

    output = stream.getvalue()
    assert "[WARN_ID] visible warning" in output
    assert "[ERR_ID] visible error" in output
    assert "[FATAL_ID] visible fatal" in output
    stats = manager.get_stats()
    assert stats.warning_count == 1
    assert stats.error_count == 1
    assert stats.fatal_count == 1


def test_fatal_logs_once_and_raises(reporting_logger):
    manager, logger, stream = reporting_logger()
    reporter = uvm_reporter(logger)

    with pytest.raises(RuntimeError):
        reporter.fatal("FATAL_ONCE", "fatal once")

    assert stream.getvalue().count("[FATAL_ONCE] fatal once") == 1
    assert manager.get_stats().fatal_count == 1


def test_severity_counts_match_reports(reporting_logger):
    manager, logger, _stream = reporting_logger()
    reporter = uvm_reporter(logger)

    reporter.info("INFO_ID", "info", UVM_LOW)
    reporter.warning("WARN_ID", "warning")
    reporter.error("ERR_ID", "error")

    stats = manager.get_stats()
    assert stats.info_count == 1
    assert stats.warning_count == 1
    assert stats.error_count == 1
    assert stats.fatal_count == 0
    assert stats.error_quit_count == 1


def test_max_quit_count_suppresses_later_report_errors(reporting_logger):
    manager, logger, stream = reporting_logger(
        policy=uvm_report_policy(max_quit_count=1)
    )
    reporter = uvm_reporter(logger)

    reporter.error("ERR_ONE", "first counted error")
    reporter.error("ERR_TWO", "suppressed after quit count")

    output = stream.getvalue()
    assert "[ERR_ONE] first counted error" in output
    assert "[MAXQUIT] Quit count reached: 1 of 1 (UVM_ERROR)" in output
    assert output.index("[ERR_ONE] first counted error") < output.index("[MAXQUIT]")
    assert "suppressed after quit count" not in output
    stats = manager.get_stats()
    assert stats.error_count == 1
    assert stats.error_quit_count == 1
    assert stats.warning_count == 0


def test_direct_logger_errors_do_not_affect_max_quit_count(reporting_logger):
    manager, logger, stream = reporting_logger(
        policy=uvm_report_policy(max_quit_count=1)
    )
    reporter = uvm_reporter(logger)

    reporter.error("ERR_ID", "counted UVM error")
    logger.error("plain direct error after quit count")

    output = stream.getvalue()
    assert "[ERR_ID] counted UVM error" in output
    assert "[MAXQUIT] Quit count reached: 1 of 1 (UVM_ERROR)" in output
    assert "plain direct error after quit count" in output
    stats = manager.get_stats()
    assert stats.error_count == 1
    assert stats.error_quit_count == 1
    assert stats.warning_count == 0


def test_max_quit_count_two_suppresses_third_report_error(reporting_logger):
    manager, logger, stream = reporting_logger(
        policy=uvm_report_policy(max_quit_count=2)
    )
    reporter = uvm_reporter(logger)

    reporter.error("ERR_ID", "first counted error")
    reporter.error("ERR_ID", "second counted error")
    reporter.error("ERR_ID", "suppressed third error")

    output = stream.getvalue()
    assert "[ERR_ID] first counted error" in output
    assert "[ERR_ID] second counted error" in output
    assert "[MAXQUIT] Quit count reached: 2 of 2 (UVM_ERROR)" in output
    assert output.index("[ERR_ID] second counted error") < output.index("[MAXQUIT]")
    assert "suppressed third error" not in output
    stats = manager.get_stats()
    assert stats.error_count == 2
    assert stats.error_quit_count == 2
    assert stats.warning_count == 0
    assert "Quit count reached: 2 of 2" in manager.failure_message("count two")


def test_large_max_quit_count_allows_errors_below_limit(reporting_logger):
    manager, logger, stream = reporting_logger(
        policy=uvm_report_policy(max_quit_count=25)
    )
    reporter = uvm_reporter(logger)

    for idx in range(8):
        reporter.error("ERR_ID", f"counted error {idx}")

    output = stream.getvalue()
    for idx in range(8):
        assert f"[ERR_ID] counted error {idx}" in output
    assert "[MAXQUIT]" not in output
    stats = manager.get_stats()
    assert stats.error_count == 8
    assert stats.error_quit_count == 8
    assert "Quit count reached" not in manager.failure_message("large count")


def test_zero_max_quit_count_allows_all_report_errors(reporting_logger):
    manager, logger, stream = reporting_logger(
        policy=uvm_report_policy(max_quit_count=0)
    )
    reporter = uvm_reporter(logger)

    for idx in range(8):
        reporter.error("ERR_ID", f"counted error {idx}")

    output = stream.getvalue()
    for idx in range(8):
        assert f"[ERR_ID] counted error {idx}" in output
    assert "[MAXQUIT]" not in output
    stats = manager.get_stats()
    assert stats.error_count == 8
    assert stats.error_quit_count == 8
    manager.log_summary(logger)
    output = stream.getvalue()
    assert "Quit count :     8 of UNLIMITED (UVM_ERROR)" in output
    assert "Quit count :     8 of     0 (UVM_ERROR)" not in output
    assert "Quit count reached" not in manager.failure_message("unlimited")


def test_demotion_changes_emitted_severity_and_counts(reporting_logger):
    manager, logger, stream = reporting_logger()
    reporter = uvm_reporter(logger)

    reporter.add_change_sev("DEMOTE_ID", "downgrade", UVM_WARNING)
    reporter.error("DEMOTE_ID", "please downgrade this")

    output = stream.getvalue()
    assert (
        "INFO:[SEVCHG] Severity changed from UVM_ERROR to UVM_WARNING "
        "for report ID 'DEMOTE_ID'"
    ) in output
    assert "WARNING:[DEMOTE_ID] please downgrade this" in output
    stats = manager.get_stats()
    assert stats.info_count == 0
    assert stats.warning_count == 1
    assert stats.error_count == 0


def test_fatal_demotion_to_error_does_not_raise(reporting_logger):
    manager, logger, stream = reporting_logger(
        policy=uvm_report_policy(max_quit_count=0)
    )
    reporter = uvm_reporter(logger)

    reporter.add_change_sev("DEMOTE_FATAL", "known fatal", UVM_ERROR)
    reporter.fatal("DEMOTE_FATAL", "known fatal downgraded")

    output = stream.getvalue()
    assert (
        "INFO:[SEVCHG] Severity changed from UVM_FATAL to UVM_ERROR "
        "for report ID 'DEMOTE_FATAL'"
    ) in output
    assert "ERROR:[DEMOTE_FATAL] known fatal downgraded" in output
    stats = manager.get_stats()
    assert stats.info_count == 0
    assert stats.error_count == 1
    assert stats.error_quit_count == 1
    assert stats.fatal_count == 0


def test_fatal_demotion_to_info_does_not_raise(reporting_logger):
    manager, logger, stream = reporting_logger()
    reporter = uvm_reporter(logger)

    reporter.add_change_sev("DEMOTE_FATAL_INFO", "known fatal", UVM_INFO)
    reporter.fatal("DEMOTE_FATAL_INFO", "known fatal waived")

    output = stream.getvalue()
    assert (
        "INFO:[SEVCHG] Severity changed from UVM_FATAL to UVM_INFO "
        "for report ID 'DEMOTE_FATAL_INFO'"
    ) in output
    assert "INFO:[DEMOTE_FATAL_INFO] known fatal waived" in output
    stats = manager.get_stats()
    assert stats.info_count == 1
    assert stats.error_count == 0
    assert stats.error_quit_count == 0
    assert stats.fatal_count == 0


def test_error_demotion_to_info_clears_error_count(reporting_logger):
    manager, logger, stream = reporting_logger()
    reporter = uvm_reporter(logger)

    reporter.add_change_sev("DEMOTE_ERROR_INFO", "known error", UVM_INFO)
    reporter.error("DEMOTE_ERROR_INFO", "known error waived")

    output = stream.getvalue()
    assert (
        "INFO:[SEVCHG] Severity changed from UVM_ERROR to UVM_INFO "
        "for report ID 'DEMOTE_ERROR_INFO'"
    ) in output
    assert "INFO:[DEMOTE_ERROR_INFO] known error waived" in output
    stats = manager.get_stats()
    assert stats.info_count == 1
    assert stats.error_count == 0
    assert stats.error_quit_count == 0
    assert stats.fatal_count == 0


def test_wildcard_report_id_demotion(reporting_logger):
    manager, logger, stream = reporting_logger()
    reporter = uvm_reporter(logger)

    reporter.add_change_sev("*", "wildcard", UVM_INFO)
    reporter.error("ANY_ID", "wildcard demotion")

    output = stream.getvalue()
    assert "INFO:[ANY_ID] wildcard demotion" in output
    stats = manager.get_stats()
    assert stats.info_count == 1
    assert stats.error_count == 0


def test_summary_text_contains_key_lines(reporting_logger):
    manager, logger, stream = reporting_logger()
    reporter = uvm_reporter(logger)

    reporter.info("INFO_ID", "info", UVM_LOW)
    reporter.warning("WARN_ID", "warning")
    stats = manager.get_stats()
    expected_counts = (
        stats.info_count,
        stats.warning_count,
        stats.error_count,
        stats.fatal_count,
        stats.error_quit_count,
    )
    manager.log_summary(logger)

    output = stream.getvalue()
    assert "--- UVM Report Summary ---" in output
    assert "** Report counts by severity" in output
    assert "UVM_INFO" in output
    assert "UVM_WARNING" in output
    assert "Quit count" in output
    assert (
        stats.info_count,
        stats.warning_count,
        stats.error_count,
        stats.fatal_count,
        stats.error_quit_count,
    ) == expected_counts


def test_final_status_defaults_to_test_status(reporting_logger):
    manager, logger, stream = reporting_logger()

    fail_msg = manager.log_final_status(logger, "status default")

    assert fail_msg is None
    output = stream.getvalue()
    assert "INFO:TEST_STATUS: PASSED" in output
    assert "DV_TEST_STATUS" not in output
    assert manager.get_stats().info_count == 0


def test_final_status_label_can_be_customized_by_policy(reporting_logger):
    manager, logger, stream = reporting_logger(
        policy=uvm_report_policy(test_status_label="DV_TEST_STATUS")
    )

    fail_msg = manager.log_final_status(
        logger, "status policy", prior_failure_msg="expected failure"
    )

    assert fail_msg == "expected failure"
    output = stream.getvalue()
    assert "INFO:DV_TEST_STATUS: FAILED" in output
    assert "INFO:TEST_STATUS: FAILED" not in output


def test_final_status_label_can_be_overridden_for_one_call(reporting_logger):
    manager, logger, stream = reporting_logger(
        policy=uvm_report_policy(test_status_label="POLICY_STATUS")
    )

    manager.log_final_status(logger, test_status_label="CALL_STATUS")

    output = stream.getvalue()
    assert "INFO:CALL_STATUS: PASSED" in output
    assert "POLICY_STATUS" not in output


def test_wrapped_formatter_includes_report_id(reporting_logger):
    _manager, logger, stream = reporting_logger(print_char_len=40)
    reporter = uvm_reporter(logger)

    reporter.info("WRAP_ID", "wrapped message", UVM_LOW)

    assert "[WRAP_ID] wrapped message" in stream.getvalue()


def test_uvm_report_formatter_uses_source_location_and_full_name(reporting_logger):
    _manager, logger, stream = reporting_logger(
        fmt="%(levelname)s:%(name)s:%(message)s"
    )
    reporter = uvm_reporter(logger, full_name="uvm_test_top.env.scoreboard")

    reporter.info("SRC_ID", "source-tagged message", UVM_LOW)

    output = stream.getvalue()
    assert "INFO:" in output
    assert "test_uvm_reporting.py(" in output
    assert "[uvm_test_top.env.scoreboard]: [SRC_ID] source-tagged message" in output


@pytest.mark.parametrize(
    ("method_name", "expected_level", "expect_exception"),
    [
        ("info", "INFO", False),
        ("warning", "WARNING", False),
        ("error", "ERROR", False),
        ("fatal", "CRITICAL", True),
    ],
)
def test_uvm_report_formatter_indents_multiline_messages(
    reporting_logger, method_name, expected_level, expect_exception
):
    _manager, logger, stream = reporting_logger(fmt="%(levelname)s:%(message)s")
    reporter = uvm_reporter(logger, full_name="uvm_test_top.env.agent1")
    report_method = getattr(reporter, method_name)

    if expect_exception:
        with pytest.raises(RuntimeError):
            report_method("MULTI_ID", "first line\nsecond line")
    elif method_name == "info":
        report_method("MULTI_ID", "first line\nsecond line", UVM_LOW)
    else:
        report_method("MULTI_ID", "first line\nsecond line")

    prefix = f"{expected_level}:"
    expected = (
        f"{prefix}[uvm_test_top.env.agent1]: [MULTI_ID] first line\n"
        f"{' ' * len(prefix)}second line"
    )
    assert expected in stream.getvalue()


def test_direct_logger_multiline_messages_are_not_uvm_reformatted(reporting_logger):
    _manager, logger, stream = reporting_logger(fmt="%(levelname)s:%(message)s")

    logger.error("first line\nsecond line")

    output = stream.getvalue()
    assert "ERROR:first line\nsecond line" in output
    assert "     second line" not in output


def test_object_uvm_report_formatter_uses_owner_full_name(reporting_logger):
    _manager, logger, stream = reporting_logger(
        fmt="%(levelname)s:%(name)s:%(message)s"
    )
    transaction = uvm_transaction("txn")
    transaction.set_report_logger(logger)

    transaction.uvm_report.info("OBJ_ID", "object report", UVM_LOW)

    output = stream.getvalue()
    assert "test_uvm_reporting.py(" in output
    assert "[txn]: [OBJ_ID] object report" in output


def test_report_summary_uses_uvm_source_location_without_counting(
    reporting_logger,
):
    manager, logger, stream = reporting_logger(fmt="%(levelname)s:%(name)s:%(message)s")
    reporter = uvm_reporter(logger, full_name="uvm_test_top")
    reporter.info("INFO_ID", "counted info", UVM_LOW)
    expected_counts = manager.get_stats().info_count

    manager.log_summary(logger)

    output = stream.getvalue()
    assert "uvm_report_server.py(" in output
    assert "[uvm_test_top]: --- UVM Report Summary ---" in output
    assert manager.get_stats().info_count == expected_counts


def test_direct_logger_keeps_logger_name_with_report_formatter(reporting_logger):
    _manager, logger, stream = reporting_logger(
        fmt="%(levelname)s:%(name)s:%(message)s"
    )

    logger.error("direct logger error")

    output = stream.getvalue()
    assert f"ERROR:{logger.name}:direct logger error" in output
    assert "test_uvm_reporting.py(" not in output


def test_direct_logger_error_is_not_counted_when_report_server_is_active(
    reporting_logger,
):
    manager, logger, stream = reporting_logger()

    logger.error("direct logger error")

    assert "ERROR:direct logger error" in stream.getvalue()
    stats = manager.get_stats()
    assert stats.error_count == 0
    assert stats.error_quit_count == 0


def test_direct_logger_error_is_not_rewritten_by_report_catcher(reporting_logger):
    manager, logger, stream = reporting_logger()

    manager.add_change_sev("*", "direct logger error", UVM_INFO)
    logger.error("direct logger error")

    assert "ERROR:direct logger error" in stream.getvalue()
    stats = manager.get_stats()
    assert stats.info_count == 0
    assert stats.error_count == 0


def test_direct_logger_error_is_not_counted_through_uvm_propagation(
    uvm_root_reporting,
):
    manager, stream = uvm_root_reporting
    child_logger = logging.getLogger("uvm.phase5.direct")
    child_logger.handlers.clear()
    child_logger.setLevel(logging.DEBUG)
    child_logger.propagate = True
    manager.register_logger(child_logger)

    child_logger.error("propagated error")

    assert stream.getvalue().count("ERROR:propagated error") == 1
    assert manager.get_stats().error_count == 0


def test_report_server_shutdown_makes_get_or_none_inactive(reporting_logger):
    manager, logger, _stream = reporting_logger()

    assert uvm_report_server.get_or_none() is manager
    manager.shutdown()

    assert uvm_report_server.get_or_none() is None
    logger.error("not counted after shutdown")
    assert manager.get_stats().error_count == 0


def test_reporter_local_catcher_applies_without_report_server():
    logger = logging.getLogger(f"uvm_reporting_test.{uuid.uuid4().hex}")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger.addHandler(handler)

    reporter = uvm_reporter(logger)
    reporter.add_change_sev("LOCAL_ID", "known issue", UVM_WARNING)
    reporter.error("LOCAL_ID", "known issue was demoted")

    assert "WARNING:[LOCAL_ID] known issue was demoted" in stream.getvalue()


def test_sv_uvm_style_reporting_mode_defaults_to_disabled():
    assert not get_sv_uvm_style_reporting_enabled()


def test_sv_uvm_style_reporting_can_be_enabled_by_plusarg(
    initialize_pyuvm, monkeypatch
):
    monkeypatch.setattr(
        cocotb,
        "plusargs",
        {"PYUVM_ENABLE_SV_UVM_STYLE_REPORTING": "1"},
        raising=False,
    )

    assert get_sv_uvm_style_reporting_enabled()
    test = uvm_test("plusarg_enabled")

    assert test.report_server is uvm_report_server.get_or_none()


@pytest.mark.parametrize("test_cls", [uvm_test, internal_uvm_test])
def test_uvm_test_does_not_auto_create_report_server_when_disabled(
    initialize_pyuvm, test_cls
):
    test_cls("disabled_test")

    assert uvm_report_server.get_or_none() is None


@pytest.mark.parametrize("test_cls", [uvm_test, internal_uvm_test])
def test_uvm_test_auto_creates_report_server_when_enabled(initialize_pyuvm, test_cls):
    set_sv_uvm_style_reporting_enabled(True)

    test = test_cls("enabled_test")
    manager = uvm_report_server.get_or_none()

    assert manager is not None
    assert test.report_server is manager
    assert manager.policy.max_quit_count == 1
    assert manager.policy.test_status_label == "TEST_STATUS"


def test_uvm_test_report_server_uses_env_runtime_options(initialize_pyuvm, monkeypatch):
    monkeypatch.setenv("UVM_VERBOSITY", "HIGH")
    monkeypatch.setenv("UVM_FAIL_ON_WARNING", "1")
    monkeypatch.setenv("UVM_FAIL_ON_ERROR", "0")
    monkeypatch.setenv("UVM_FAIL_ON_FATAL", "0")
    monkeypatch.setenv("max_quit_count", "9")
    monkeypatch.setenv("TEST_STATUS_LABEL", "ENV_STATUS")
    monkeypatch.setenv("print_char_len", "64")
    set_sv_uvm_style_reporting_enabled(True)

    uvm_test("env_options_test")
    manager = uvm_report_server.get_or_none()

    assert manager is not None
    assert manager.verbosity == UVM_HIGH
    assert manager.policy.fail_on_warning
    assert not manager.policy.fail_on_error
    assert not manager.policy.fail_on_fatal
    assert manager.policy.max_quit_count == 9
    assert manager.policy.test_status_label == "ENV_STATUS"
    assert manager._print_char_len == 64


def test_uvm_test_report_server_plusargs_override_env_options(
    initialize_pyuvm, monkeypatch
):
    monkeypatch.setenv("UVM_VERBOSITY", "LOW")
    monkeypatch.setenv("max_quit_count", "3")
    monkeypatch.setenv("TEST_STATUS_LABEL", "ENV_STATUS")
    monkeypatch.setattr(
        cocotb,
        "plusargs",
        {
            "UVM_VERBOSITY": "FULL",
            "max_quit_count": "7",
            "test_status_label": "PLUS_STATUS",
            "print_char_len": "42",
        },
        raising=False,
    )
    set_sv_uvm_style_reporting_enabled(True)

    uvm_test("plusarg_options_test")
    manager = uvm_report_server.get_or_none()

    assert manager is not None
    assert manager.verbosity == UVM_FULL
    assert manager.policy.max_quit_count == 7
    assert manager.policy.test_status_label == "PLUS_STATUS"
    assert manager._print_char_len == 42


def test_uvm_test_add_message_demotes_hook_is_called(initialize_pyuvm):
    class HookTest(uvm_test):
        def add_message_demotes(self, catcher):
            super().add_message_demotes(catcher)
            self.hook_catcher = catcher
            catcher.add_change_sev("HOOK_ID", "known issue", UVM_INFO)

    set_sv_uvm_style_reporting_enabled(True)

    test = HookTest("hook_test")
    manager = uvm_report_server.get_or_none()
    test.uvm_report.error("HOOK_ID", "known issue is waived")

    assert manager is not None
    assert test.hook_catcher is manager.catcher
    stats = manager.get_stats()
    assert stats.info_count == 1
    assert stats.error_count == 0


@pytest.mark.parametrize(
    ("method_name", "new_severity", "expected_info", "expected_error"),
    [
        ("fatal", UVM_ERROR, 0, 1),
        ("fatal", UVM_INFO, 1, 0),
        ("error", UVM_INFO, 1, 0),
    ],
)
def test_uvm_test_hook_installed_demotions_rewrite_reports(
    initialize_pyuvm, method_name, new_severity, expected_info, expected_error
):
    class DemoteTest(uvm_test):
        def add_message_demotes(self, catcher):
            super().add_message_demotes(catcher)
            catcher.add_change_sev("DEMOTE_ID", "known mismatch", new_severity)

    set_sv_uvm_style_reporting_enabled(True)

    test = DemoteTest("demote_test")
    manager = uvm_report_server.get_or_none()
    getattr(test.uvm_report, method_name)("DEMOTE_ID", "known mismatch")

    assert manager is not None
    stats = manager.get_stats()
    assert stats.info_count == expected_info
    assert stats.error_count == expected_error
    assert stats.fatal_count == 0


def test_legacy_report_object_creates_default_stream_handler():
    report_object = uvm_report_object("report_object")

    assert not report_object.logger.propagate
    assert report_object._streaming_handler in report_object.logger.handlers
    assert isinstance(report_object._streaming_handler, logging.StreamHandler)


def test_legacy_remove_streaming_handler_removes_default_handler():
    report_object = uvm_report_object("report_object")
    streaming_handler = report_object._streaming_handler

    report_object.remove_streaming_handler()

    assert report_object._streaming_handler is None
    assert streaming_handler not in report_object.logger.handlers


def test_legacy_disable_logging_installs_null_handler():
    report_object = uvm_report_object("report_object")

    report_object.disable_logging()

    assert report_object._streaming_handler is None
    assert not report_object.logger.propagate
    assert any(
        isinstance(handler, logging.NullHandler)
        for handler in report_object.logger.handlers
    )


def test_legacy_custom_handler_receives_logger_messages():
    report_object = uvm_report_object("report_object")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)

    try:
        report_object.add_logging_handler(handler)
        report_object.logger.info("custom logger message")

        assert "custom logger message" in stream.getvalue()
    finally:
        report_object.remove_logging_handler(handler)
        handler.close()


def test_sv_uvm_style_report_object_does_not_create_default_stream_handler():
    set_sv_uvm_style_reporting_enabled(True)
    report_object = uvm_report_object("report_object")

    assert report_object.logger.propagate
    assert report_object._streaming_handler is None
    assert not any(
        getattr(handler, "_pyuvm_object_default_handler", False)
        for handler in report_object.logger.handlers
    )


def test_sv_uvm_style_report_object_removes_reused_logger_stream_handler():
    logger_name = f"reused_report_object.{uuid.uuid4().hex}"
    logger = logging.getLogger(f"uvm.{logger_name}")

    class ReusedLoggerReportObject(uvm_report_object):
        def get_initial_logger_name(self):
            return logger_name

    try:
        legacy_report_object = ReusedLoggerReportObject("legacy_report_object")
        assert any(
            isinstance(handler, logging.StreamHandler)
            for handler in legacy_report_object.logger.handlers
        )

        set_sv_uvm_style_reporting_enabled(True)
        report_object = ReusedLoggerReportObject("report_object")

        assert report_object.logger is logger
        assert report_object.logger.propagate
        assert report_object._streaming_handler is None
        assert not report_object.logger.handlers
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def test_uvm_report_uses_existing_object_verbosity():
    transaction = uvm_transaction("transaction")

    transaction.set_report_verbosity(UVM_HIGH)

    assert transaction.uvm_verbosity == UVM_HIGH
    assert transaction.uvm_report.verbosity == UVM_HIGH


def test_object_report_verbosity_updates_global_server(reporting_logger):
    manager, logger, stream = reporting_logger(verbosity=UVM_LOW)
    first = uvm_transaction("first")
    second = uvm_transaction("second")
    first.set_report_logger(logger.getChild("first"))
    second.set_report_logger(logger.getChild("second"))

    first.set_report_verbosity(UVM_HIGH)

    first.uvm_report.info("FIRST", "local high visible", UVM_HIGH)
    second.uvm_report.info("SECOND", "global high shows high", UVM_HIGH)

    output = stream.getvalue()
    assert "[FIRST] local high visible" in output
    assert "[SECOND] global high shows high" in output
    assert manager.verbosity == UVM_HIGH
    assert manager.get_stats().info_count == 2


def test_pre_server_report_verbosity_does_not_override_created_server():
    set_sv_uvm_style_reporting_enabled(True)
    logger = logging.getLogger("uvm")
    old_level = logger.level
    old_propagate = logger.propagate
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger.addHandler(handler)

    transaction = uvm_transaction("transaction")
    transaction.set_report_verbosity(UVM_HIGH)
    report = transaction.uvm_report

    manager = uvm_report_server.create(root_logger=logger, verbosity=UVM_LOW)
    try:
        report.info("LOCAL_BEFORE_SERVER", "hidden after server starts", UVM_HIGH)
        report.info("LOCAL_BEFORE_SERVER", "visible low report", UVM_LOW)

        output = stream.getvalue()
        assert "[LOCAL_BEFORE_SERVER] hidden after server starts" not in output
        assert "[LOCAL_BEFORE_SERVER] visible low report" in output
        assert manager.verbosity == UVM_LOW
    finally:
        manager.shutdown()
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        logger.propagate = old_propagate


def test_component_supports_uvm_report(initialize_pyuvm, uvm_root_reporting):
    _manager, stream = uvm_root_reporting
    component = uvm_component("component", None)

    component.uvm_report.info("COMP_ID", "component report", UVM_LOW)

    assert "[COMP_ID] component report" in stream.getvalue()


@pytest.mark.parametrize(
    ("cls", "name", "message"),
    [
        (uvm_sequence, "sequence", "sequence report"),
        (uvm_sequence_item, "sequence_item", "sequence item report"),
        (uvm_transaction, "transaction", "transaction report"),
    ],
)
def test_non_component_objects_support_uvm_report(
    cls, name, message, uvm_root_reporting
):
    _manager, stream = uvm_root_reporting
    obj = cls(name)

    obj.uvm_report.info("OBJ_ID", message, UVM_LOW)

    assert f"[OBJ_ID] {message}" in stream.getvalue()
