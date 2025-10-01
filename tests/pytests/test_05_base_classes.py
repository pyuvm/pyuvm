import copy

import pytest

from pyuvm import *

pytestmark = pytest.mark.usefixtures("initialize_pyuvm")


class my_object(uvm_object):
    def __init__(self, name=""):
        super().__init__(name)
        self.val = 5

    def __eq__(self, other):
        if type(other) is type(self):
            return self.val == other.val

    def __str__(self):
        return "Hello"

    def do_copy(self, other):
        self.val = other.val


def test_basic_creation():
    """
    15.3
    Tests whether the factory gets populated and whether it can be used.
    """
    uvf = uvm_factory()
    mof = uvf.fd.classes["my_object"]("factory")
    moi = my_object("name")
    assert type(mof) == type(moi)


# Testing specification


def test_seeding():
    """
    5.3.3.1 get_uvm_seeding
    5.3.3.2 set_uvm_seeding
    5.3.3.3 reseed
    """
    mo = my_object("mo")
    with pytest.raises(error_classes.UVMNotImplemented):
        mo.get_uvm_seeding()
    with pytest.raises(error_classes.UVMNotImplemented):
        _ = mo.set_uvm_seeding(1)
    with pytest.raises(error_classes.UVMNotImplemented):
        mo.reseed()


def test_identification():
    """
    5.3.4
    :return:
    """
    nameless = my_object()
    assert len(nameless.get_name()) == 0
    moe = my_object("moe")
    # 5.3.4.2
    name = moe.get_name()
    assert "moe" == name
    # 5.3.4.1
    moe.set_name("curly")
    name = moe.get_name()
    assert "curly" == name
    moe.set_name("larry")
    # 5.3.4.3
    name = moe.get_full_name()
    assert "larry" == name
    # 5.3.4.4
    moe_id = moe.get_inst_id()
    assert id(moe) == moe_id
    # 5.3.4.5 not implemented
    with pytest.raises(error_classes.UsePythonMethod):
        moe.get_type()
    # 5.3.4.6 not implemented
    with pytest.raises(error_classes.UsePythonMethod):
        moe.get_object_type()
    # 5.3.4.7
    assert "my_object" == moe.get_type_name()


def test_creation():
    """
    5.3.5
    :return:
    """
    mo = my_object("mo")
    # 5.3.5.1
    new_mo = mo.create("new_mo")
    assert "new_mo" == new_mo.get_name()
    assert type(new_mo) == type(mo)
    # 5.3.5.2
    mo.val = 5
    cln_mo = copy.deepcopy(mo)
    assert mo.__eq__(cln_mo)


def test_printing():
    """
    5.3.6
    :return:
    """
    mo = my_object("mo")
    # 5.3.6.1
    with pytest.raises(error_classes.UsePythonMethod):
        mo.print()
    # 5.3.6.2
    with pytest.raises(error_classes.UsePythonMethod):
        mo.sprint()
    assert "Hello", mo.convert2string()


def test_recording():
    """
    5.3.7
    :return:
    """
    mo = my_object("mo")
    # 5.3.7.1
    with pytest.raises(error_classes.UVMNotImplemented):
        mo.record()
    # 5.3.7.2
    with pytest.raises(error_classes.UVMNotImplemented):
        mo.do_record()


def test_copying():
    """
    5.3.8
    :return:
    """
    mo = my_object("mo")
    rhs = my_object("rhs")
    # 5.3.8.1
    mo.copy(rhs)
    # 5.3.8.2
    assert mo.val == rhs.val


def test_comparing():
    """
    5.3.9
    :return:
    """
    mo = my_object("mo")
    rhs = my_object("rhs")
    # 5.3.9.1
    assert mo.compare(rhs)
    # 5.3.9.2
    assert mo.do_compare(rhs)


def test_packing():
    """
    5.3.10
    :return:
    """
    mo = my_object("mo")
    # 5.3.10.1
    with pytest.raises(error_classes.UsePythonMethod):
        mo.pack()
    with pytest.raises(error_classes.UsePythonMethod):
        mo.pack_bytes()
    with pytest.raises(error_classes.UsePythonMethod):
        mo.pack_ints()
    with pytest.raises(error_classes.UsePythonMethod):
        mo.pack_longints()
    # 5.3.10.2
    with pytest.raises(error_classes.UsePythonMethod):
        mo.do_pack()


def test_unpacking():
    """
    5.3.11
    :return:
    """
    mo = my_object("mo")
    # 5.3.10.1
    with pytest.raises(error_classes.UsePythonMethod):
        mo.unpack()
    with pytest.raises(error_classes.UsePythonMethod):
        mo.unpack_bytes()
    with pytest.raises(error_classes.UsePythonMethod):
        mo.unpack_ints()
    with pytest.raises(error_classes.UsePythonMethod):
        mo.unpack_longints()
    # 5.3.11.2

    with pytest.raises(error_classes.UsePythonMethod):
        mo.do_unpack()


def test_configuration():
    """
    5.3.12
    :return:
    """
    mo = my_object("mo")
    # 5.3.12.1
    with pytest.raises(error_classes.UsePythonMethod):
        mo.set_local()


def test_field_operations():
    """
    5.3.13
    :return:
    """
    mo = my_object("mo")
    with pytest.raises(error_classes.UsePythonMethod):
        mo.do_execute_op(None)


def test_active_policy():
    """
    5.3.14
    :return:
    """
    mo = my_object("mo")
    with pytest.raises(error_classes.UVMNotImplemented):
        mo.push_active_policy()
    with pytest.raises(error_classes.UVMNotImplemented):
        mo.pop_active_policy()
    with pytest.raises(error_classes.UVMNotImplemented):
        mo.get_active_policy()


def test_create():
    """
    5.3.5 This needs to be further implemented to include the factory
    """
    mo = my_object("first")
    mo2 = mo.create("second")
    assert mo == mo2


def test_uvm_transaction_creation():
    """
    5.4.2.1
    5.4.2.14
    5.4.2.15
    :return:
    """
    tr = uvm_transaction()
    assert 0 == len(tr.get_name())
    assert not tr.get_initiator()
    uc = uvm_component("uc", None)
    tr.set_initiator(uc)
    assert uc == tr.get_initiator()


def test_transaction_recording():
    """
    5.4.2 all methods
    :return:
    """
    tr = uvm_transaction()
    with pytest.raises(error_classes.UVMNotImplemented):
        tr.get_tr_handle()
    with pytest.raises(error_classes.UVMNotImplemented):
        tr.enable_recording()
    with pytest.raises(error_classes.UVMNotImplemented):
        tr.disable_recording()
    with pytest.raises(error_classes.UVMNotImplemented):
        tr.is_recording_enabled()
    with pytest.raises(error_classes.UVMNotImplemented):
        tr.is_active()
    with pytest.raises(error_classes.UVMNotImplemented):
        tr.get_event_pool()
    tr.get_accept_time()
    tr.get_begin_time()
    tr.get_end_time()


def test_clone():
    orig = my_object("orig")
    clone = orig.clone()
    assert id(orig) != id(clone)
    assert orig.val == clone.val
