import io
import logging
import uuid

import pytest

from pyuvm import (
    UVM_HIGH,
    UVM_INFO,
    UVM_LOW,
    UVM_NONE,
    UVM_WARNING,
    get_sv_uvm_style_reporting_enabled,
    set_sv_uvm_style_reporting_enabled,
    uvm_component,
    uvm_report_object,
    uvm_report_server,
    uvm_reporter,
    uvm_sequence,
    uvm_sequence_item,
    uvm_transaction,
)


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

    def make(verbosity=UVM_LOW, print_char_len=300):
        name = f"uvm_reporting_test.{uuid.uuid4().hex}"
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
        logger.addHandler(handler)

        manager = uvm_report_server.create(
            root_logger=logger,
            verbosity=verbosity,
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


def test_demotion_changes_emitted_severity_and_counts(reporting_logger):
    manager, logger, stream = reporting_logger()
    reporter = uvm_reporter(logger)

    reporter.add_change_sev("DEMOTE_ID", "downgrade", UVM_WARNING)
    reporter.error("DEMOTE_ID", "please downgrade this")

    output = stream.getvalue()
    assert "WARNING:[DEMOTE_ID] please downgrade this" in output
    stats = manager.get_stats()
    assert stats.warning_count == 1
    assert stats.error_count == 0


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
    manager.log_summary(logger)

    output = stream.getvalue()
    assert "--- UVM Report Summary ---" in output
    assert "** Report counts by severity" in output
    assert "UVM_INFO" in output
    assert "UVM_WARNING" in output
    assert "Quit count" in output


def test_wrapped_formatter_includes_report_id(reporting_logger):
    _manager, logger, stream = reporting_logger(print_char_len=40)
    reporter = uvm_reporter(logger)

    reporter.info("WRAP_ID", "wrapped message", UVM_LOW)

    assert "[WRAP_ID] wrapped message" in stream.getvalue()


def test_direct_logger_error_is_counted_when_report_server_is_active(reporting_logger):
    manager, logger, _stream = reporting_logger()

    logger.error("direct logger error")

    stats = manager.get_stats()
    assert stats.error_count == 1
    assert stats.error_quit_count == 1


def test_direct_logger_error_is_counted_once_through_uvm_propagation(
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
    assert manager.get_stats().error_count == 1


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

    report_object.add_logging_handler(handler)
    report_object.logger.info("custom logger message")

    assert "custom logger message" in stream.getvalue()


def test_sv_uvm_style_report_object_does_not_create_default_stream_handler():
    set_sv_uvm_style_reporting_enabled(True)
    report_object = uvm_report_object("report_object")

    assert report_object.logger.propagate
    assert report_object._streaming_handler is None
    assert not any(
        getattr(handler, "_pyuvm_object_default_handler", False)
        for handler in report_object.logger.handlers
    )


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
