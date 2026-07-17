"""Tests for ObjectionHandler count-based phase-end gating.

IEEE 1800.2 section 10.5 defines objection handling in terms of a running
count: raising increments and dropping decrements, and a phase may end only
once the count returns to zero. These tests exercise that count directly
(without a running simulation) plus the pyuvm-specific hardening around a
drop with no matching raise.
"""

import pytest

from pyuvm import ObjectionHandler


class fake_component:
    """Minimal stand-in for a uvm_component: objections key off get_full_name."""

    def __init__(self, name):
        self._name = name

    def get_full_name(self):
        return self._name


@pytest.fixture(autouse=True)
def clean_objections():
    """ObjectionHandler is a singleton not covered by clear_singletons."""
    ObjectionHandler().clear()
    yield
    ObjectionHandler().clear()


def test_count_tracks_raises_and_drops():
    """
    10.5 The outstanding objection count increments on raise and decrements
    on drop.
    """
    oh = ObjectionHandler()
    comp = fake_component("env.agent")
    assert oh.get_objection_count() == 0
    oh.raise_objection(comp, "first")
    oh.raise_objection(comp, "second")
    assert oh.get_objection_count() == 2
    oh.drop_objection(comp, "")
    assert oh.get_objection_count() == 1
    oh.drop_objection(comp, "")
    assert oh.get_objection_count() == 0


def test_count_spans_multiple_components():
    """
    10.5 The count aggregates objections across all components; the phase is
    not complete until every component has dropped. This is the multi-raiser
    case that a per-component "is this component's list empty" check missed.
    """
    oh = ObjectionHandler()
    top = fake_component("uvm_test_top")
    sub = fake_component("uvm_test_top.sub")
    oh.raise_objection(top, "top objects")
    oh.raise_objection(sub, "sub objects")
    assert oh.get_objection_count() == 2
    # Dropping one component's objection must not zero the global count while
    # the other component is still objecting.
    oh.drop_objection(top, "")
    assert oh.get_objection_count() == 1
    oh.drop_objection(sub, "")
    assert oh.get_objection_count() == 0


def test_raise_drop_same_slot_is_balanced():
    """
    A run_phase that raises then immediately drops (within one scheduler slot)
    must leave the count at zero -- the regression that motivated moving from
    an edge-triggered flag to a real count.
    """
    oh = ObjectionHandler()
    comp = fake_component("env")
    oh.raise_objection(comp, "brief")
    oh.drop_objection(comp, "")
    assert oh.get_objection_count() == 0
    # The "was an objection ever raised" flag stays set for the phase-end
    # warning logic even though the count is back to zero.
    assert oh.objection_raised is True


def test_unmatched_drop_is_noop():
    """
    A drop with no matching raise must not go negative or crash; it is a
    logged no-op. (Guards against the earlier uncaught KeyError / count
    corruption.)
    """
    oh = ObjectionHandler()
    comp = fake_component("stray")
    oh.drop_objection(comp, "never raised")
    assert oh.get_objection_count() == 0


def test_extra_drop_after_balance_is_noop():
    """
    An extra drop after the count is already zero stays a no-op rather than
    driving the count negative.
    """
    oh = ObjectionHandler()
    comp = fake_component("env")
    oh.raise_objection(comp, "one")
    oh.drop_objection(comp, "")
    oh.drop_objection(comp, "")  # one too many
    assert oh.get_objection_count() == 0


def test_clear_resets_count_and_flag():
    """clear() resets both the outstanding count and the raised flag."""
    oh = ObjectionHandler()
    comp = fake_component("env")
    oh.raise_objection(comp, "one")
    assert oh.get_objection_count() == 1
    oh.clear()
    assert oh.get_objection_count() == 0
    assert oh.objection_raised is False
