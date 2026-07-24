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

    __hash__: None  # type: ignore[assignment]

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
    assert type(mof) is type(moi)


# Testing specification


def test_seeding():
    """
    5.3.3.1 get_uvm_seeding
    5.3.3.2 set_uvm_seeding
    5.3.3.3 reseed
    """
    mo = my_object("mo")
    with pytest.raises(UVMNotImplemented):
        mo.get_uvm_seeding()
    with pytest.raises(UVMNotImplemented):
        _ = mo.set_uvm_seeding(1)
    with pytest.raises(UVMNotImplemented):
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
    with pytest.raises(UsePythonMethod):
        moe.get_type()
    # 5.3.4.6 not implemented
    with pytest.raises(UsePythonMethod):
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
    assert type(new_mo) is type(mo)
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
    with pytest.raises(UsePythonMethod):
        mo.print()
    # 5.3.6.2
    with pytest.raises(UsePythonMethod):
        mo.sprint()
    assert "Hello" == mo.convert2string()


def test_recording():
    """
    5.3.7
    :return:
    """
    mo = my_object("mo")
    # 5.3.7.1
    with pytest.raises(UVMNotImplemented):
        mo.record()
    # 5.3.7.2
    with pytest.raises(UVMNotImplemented):
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
    # Distinct objects must compare unequal, and compare()/do_compare()
    # must return a real bool (not the truthy NotImplemented sentinel that
    # object.__eq__ yields when no __eq__ is defined).
    a = uvm_object("a")
    b = uvm_object("b")
    assert a.compare(b) is False
    assert a.do_compare(b) is False
    assert a.compare(a) is True


def test_packing():
    """
    5.3.10
    :return:
    """
    mo = my_object("mo")
    # 5.3.10.1
    with pytest.raises(UsePythonMethod):
        mo.pack()
    with pytest.raises(UsePythonMethod):
        mo.pack_bytes()
    with pytest.raises(UsePythonMethod):
        mo.pack_ints()
    with pytest.raises(UsePythonMethod):
        mo.pack_longints()
    # 5.3.10.2
    with pytest.raises(UsePythonMethod):
        mo.do_pack()


def test_unpacking():
    """
    5.3.11
    :return:
    """
    mo = my_object("mo")
    # 5.3.10.1
    with pytest.raises(UsePythonMethod):
        mo.unpack()
    with pytest.raises(UsePythonMethod):
        mo.unpack_bytes()
    with pytest.raises(UsePythonMethod):
        mo.unpack_ints()
    with pytest.raises(UsePythonMethod):
        mo.unpack_longints()
    # 5.3.11.2

    with pytest.raises(UsePythonMethod):
        mo.do_unpack()


def test_configuration():
    """
    5.3.12
    :return:
    """
    mo = my_object("mo")
    # 5.3.12.1
    with pytest.raises(UsePythonMethod):
        mo.set_local()


def test_field_operations():
    """
    5.3.13
    :return:
    """
    mo = my_object("mo")
    with pytest.raises(UsePythonMethod):
        mo.do_execute_op(None)


def test_active_policy():
    """
    5.3.14
    :return:
    """
    mo = my_object("mo")
    with pytest.raises(UVMNotImplemented):
        mo.push_active_policy()
    with pytest.raises(UVMNotImplemented):
        mo.pop_active_policy()
    with pytest.raises(UVMNotImplemented):
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
    with pytest.raises(UVMNotImplemented):
        tr.get_tr_handle()
    with pytest.raises(UVMNotImplemented):
        tr.enable_recording()
    with pytest.raises(UVMNotImplemented):
        tr.disable_recording()
    with pytest.raises(UVMNotImplemented):
        tr.is_recording_enabled()
    with pytest.raises(UVMNotImplemented):
        tr.is_active()
    with pytest.raises(UVMNotImplemented):
        tr.get_event_pool()
    # Reading a time before its stage has occurred raises rather than
    # returning a sentinel (Python has exceptions; SV-UVM's -1 does not apply).
    with pytest.raises(UVMError):
        tr.get_accept_time()
    with pytest.raises(UVMError):
        tr.get_begin_time()
    with pytest.raises(UVMError):
        tr.get_end_time()


def test_transaction_time_getters_after_set():
    """
    5.4.2.4/5/6 get_accept_time/get_begin_time/get_end_time return the
    recorded time once the corresponding stage has run.
    """
    tr = uvm_transaction("tr")
    tr.accept_tr(10)
    assert tr.get_accept_time() == 10
    tr.begin_tr(20)
    assert tr.get_begin_time() == 20
    tr.end_tr(30)
    assert tr.get_end_time() == 30


def test_begin_tr_without_accept_does_not_raise():
    """
    5.4.2.5 begin_tr enforces begin_time >= accept_time, but only when
    accept_tr() has actually been called. A begin_tr with no prior accept_tr
    must not raise (there is no accept constraint to violate).
    """
    tr = uvm_transaction("tr")
    # No accept_tr(); a positive begin_time must be accepted, not compared
    # against a missing accept_time.
    tr.begin_tr(5)
    assert tr.get_begin_time() == 5


def test_begin_tr_before_accept_time_is_fatal():
    """
    5.4.2.5 begin_time earlier than a recorded accept_time is illegal.
    """
    tr = uvm_transaction("tr")
    tr.accept_tr(10)
    with pytest.raises(UVMFatalError):
        tr.begin_tr(5)


def test_end_tr_without_begin_does_not_raise():
    """
    5.4.2.6 end_tr enforces end_time >= accept_time and >= begin_time, but
    each ordering check applies only if that earlier stage occurred. An
    end_tr with no prior accept_tr/begin_tr must not raise.
    """
    tr = uvm_transaction("tr")
    tr.end_tr(5)
    assert tr.get_end_time() == 5


def test_end_tr_before_begin_time_is_fatal():
    """
    5.4.2.6 end_time earlier than a recorded begin_time is illegal.
    """
    tr = uvm_transaction("tr")
    tr.accept_tr(1)
    tr.begin_tr(10)
    with pytest.raises(UVMFatalError):
        tr.end_tr(5)


def test_clone():
    orig = my_object("orig")
    clone = orig.clone()
    assert id(orig) != id(clone)
    assert orig.val == clone.val


def test_uvm_component_parent_default(initialize_pyuvm):
    # IEEE 1800.2 declares ``new(name, parent=null)``; uvm_component should
    # match that signature and resolve a missing parent to uvm_root.
    uc = uvm_component("c_default")
    assert uc.parent is uvm_root()


def test_uvm_sequencer_parent_default(initialize_pyuvm):
    # The constructor of uvm_sequencer was missing the default parent
    # argument expected by the IEEE 1800.2 signature
    # ``new(name, parent=null)``. See pyuvm issue #299.
    seq = uvm_sequencer("seqr_default")
    assert seq.parent is uvm_root()
