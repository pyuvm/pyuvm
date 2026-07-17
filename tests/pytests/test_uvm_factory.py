"""Tests for uvm_factory override handling.

Covers two IEEE 1800.2 section 8.3.1.4.2 behaviors plus a diagnostic-path
robustness fix:
- set_type_override_*(replace=False) must still install a type override when
  only an *instance* override previously existed for that original.
- str(uvm_factory()) must not crash when an override was keyed by an arbitrary
  string (a name-based override of an unregistered original).
"""

import pytest

from pyuvm import uvm_component, uvm_factory


class Orig(uvm_component): ...


class InstOv(uvm_component): ...


class TypeOv(uvm_component): ...


class OtherTypeOv(uvm_component): ...


@pytest.fixture(autouse=True)
def clean_factory():
    uvm_factory().clear_overrides()
    yield
    uvm_factory().clear_overrides()


def test_type_override_applies_when_only_inst_override_exists():
    """
    8.3.1.4.2 replace=False means "do not clobber an existing *type* override".
    An instance override is not a type override, so a later type override with
    replace=False must still be installed.
    """
    f = uvm_factory()
    f.set_inst_override_by_type(Orig, InstOv, "a.b.c")
    assert f.fd.overrides[Orig].type_override is None

    f.set_type_override_by_type(Orig, TypeOv, replace=False)
    assert f.fd.overrides[Orig].type_override is TypeOv
    # The pre-existing instance override is untouched.
    assert f.fd.overrides[Orig].inst_overrides["a.b.c"] is InstOv


def test_type_override_replace_false_protects_existing_type_override():
    """
    8.3.1.4.2 replace=False must not overwrite an existing type override, while
    replace=True must.
    """
    f = uvm_factory()
    f.set_type_override_by_type(Orig, TypeOv)
    f.set_type_override_by_type(Orig, OtherTypeOv, replace=False)
    assert f.fd.overrides[Orig].type_override is TypeOv
    f.set_type_override_by_type(Orig, OtherTypeOv, replace=True)
    assert f.fd.overrides[Orig].type_override is OtherTypeOv


def test_type_override_by_name_applies_over_inst_override():
    """
    8.3.1.4.2 same replace=False semantics via the name-based API.
    """
    f = uvm_factory()
    f.set_inst_override_by_type(Orig, InstOv, "x.y")
    f.set_type_override_by_name("Orig", "TypeOv", replace=False)
    assert f.fd.overrides[Orig].type_override is TypeOv


def test_str_does_not_crash_on_string_override_key():
    """
    A name-based override of an unregistered original stores an arbitrary
    string as the override key. str(uvm_factory()) must render it (the key has
    no __name__) rather than raising AttributeError.
    """
    f = uvm_factory()
    f.set_type_override_by_name("not_a_registered_class", "TypeOv")
    text = str(f)  # must not raise
    assert "not_a_registered_class" in text
