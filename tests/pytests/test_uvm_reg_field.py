# Main Packages for the entire RAL model
import pytest
from pyuvm.s17_uvm_reg_enumerations import uvm_predict_e, uvm_door_e
from pyuvm.s27_uvm_reg_pkg import uvm_reg_field, uvm_reg
from pyuvm.s24_uvm_reg_includes import predict_t, access_e
from pyuvm.s24_uvm_reg_includes import uvm_resp_t, path_t

##############################################################################
# TIPS
##############################################################################
"""
Use this to execute the test which will not be
counted into the entire number of FAILING tests
@pytest.mark.xfail

Use this to just skip the execution of a specific test
@pytest.mark.skip

Use this to give a specific test method a
name ID the exeucte it by using py.test -m ID_NAME
@pytest.mark.ID_NAME

Use this to give a specific test parameters to be used
@pytest.mark.parametrize("name1, name2",value_type_1, value_type_2)

If pip install pytest-sugar is ran then pytest is gonna
likly execute a bar progression while
running tests (expecially if in Parallel)
"""

##############################################################################
# TESTS
##############################################################################


##############################################################################
# TESTS uvm_reg_field
##############################################################################


@pytest.mark.test_reg_field_get_name
def test_reg_field_get_name():
    field_with_explicit_name = uvm_reg_field("some_field")
    assert field_with_explicit_name.get_name() == "some_field"
    field_with_implicit_name = uvm_reg_field()
    assert field_with_implicit_name.get_name() == 'uvm_reg_field'


@pytest.mark.test_reg_field_configure
def test_reg_field_configure():
    field = uvm_reg_field()
    parent = uvm_reg()
    field.configure(parent, 8, 16, 'RW', True, 15)
    field.field_lock()
    assert field.get_parent() == parent
    assert field.get_n_bits() == 8
    assert field.get_lsb_pos() == 16
    assert field.get_access() == 'RW'
    assert field.is_volatile()
    assert field.get_reset() == 15

@pytest.mark.test_reg_field_is_volatile
def test_reg_field_is_volatile():
    field = uvm_reg_field("FIELD_volatile")
    field.configure(uvm_reg(), 8, 16, 'RW', True, 15)
    field.field_lock()
    assert field.is_volatile()
    field.configure(uvm_reg(), 8, 16, 'RW', False, 15)
    field.field_lock()
    assert not field.is_volatile()

@pytest.mark.test_reg_field_all_access
def test_reg_field_all_access():
    for acs in ["RO","RW","RC","RS","WC","WS","W1C","W1S","W1T","W0C","W0S","W0T","WRC","WRS","W1SRC","W1CRS","W0SRC","W0CRS","WSRC","WCRS","WO","WOC","WOS","W1","WO1"]:
        field = uvm_reg_field("FIELD_"+acs)
        field.configure(uvm_reg(), 8, 16, acs, True, 15)
        field.field_lock()
        assert field.get_access() == acs, "Access value {} not in the list".format(acs)

@pytest.mark.test_reg_field_lsb_pos
def test_reg_field_lsb_pos():
    field = uvm_reg_field("FIELD_lsb_pos")
    field.configure(uvm_reg(), 8, 16, 'RW', True, 15)
    field.field_lock()
    assert field.get_lsb_pos() == 16

@pytest.mark.test_reg_field_reset
def test_reg_field_reset():
    field = uvm_reg_field()
    field.configure(uvm_reg(), 8, 16, 'RW', True, 15)
    field.field_lock()
    field.reset()
    assert field.get_reset() == 15, "after reset internal reset value doesn't match {}".format(field.get_reset())
    assert field.get_value() == 15, "after reset internal mirrored value doesn't match {}".format(field.get_value())

@pytest.mark.test_reg_field_get
def test_reg_field_get():
    field = uvm_reg_field()
    field.configure(uvm_reg(), 8, 16, 'RW', True, 15)
    field.field_lock()
    assert field.get() == 0

@pytest.mark.test_reg_field_get_value
def test_reg_field_get_value():
    field = uvm_reg_field()
    field.configure(uvm_reg(), 8, 16, 'RW', True, 15)
    field.field_lock()
    assert field.get_lsb_pos() == 16

@pytest.mark.test_reg_field_field_predict_read_set
def test_reg_field_field_predict_read_set():
    from random import randint
    field = uvm_reg_field()
    ## With the set register once we perfom the operation R the register will be set entirely according to the fields
    ## getting a prendicted value of 1 regardless of the predicted value we set through the function
    for acs in ["RS","WRS","WCRS","W1CRS","W0CRS"]:
        field.configure(uvm_reg(), 8, 16, acs, True, 15)
        field.field_lock()
        field.reset()
        field.predict(randint(1,2**field.get_n_bits()), kind=uvm_predict_e.UVM_PREDICT_READ, path=uvm_door_e.UVM_FRONTDOOR)
        assert field.get_value() == (2**field.get_n_bits()-1), "Failing for access {}".format(acs)
        assert field.get_response() == uvm_resp_t.PASS_RESP, "Failing as default status is not PASS_RESP is {}".format(field.get_response())

@pytest.mark.test_reg_field_field_predict_read_clear
def test_reg_field_field_predict_read_clear():
    from random import randint
    field = uvm_reg_field()
    ## With the clear register once we perfom the operation R the register will be cleared entirely according to the fields
    ## getting a prendicted value of 0 regardless of the predicted value we set through the function
    for acs in ["RC","WRC","WSRC","W1SRC","W0SRC"]:
        field.configure(uvm_reg(), 8, 16, acs, True, 15)
        field.field_lock()
        field.reset()
        field.predict(randint(1,2**field.get_n_bits()), kind=uvm_predict_e.UVM_PREDICT_READ, path=uvm_door_e.UVM_FRONTDOOR)
        assert field.get_value() == 0, "Failing for access {}".format(acs)
        assert field.get_response() == uvm_resp_t.PASS_RESP, "Failing as default status is not PASS_RESP is {}".format(field.get_response())

@pytest.mark.test_reg_field_field_predict_write_set
def test_reg_field_field_predict_write_set():
    from random import randint
    field = uvm_reg_field()
    ## With the set register once we perfom the operation W the register will be set entirely according to the fields
    ## getting a prendicted value of 1 regardless of the predicted value we set through the function
    for acs in ["WSRC", "WOS", "WS", "W0S", "W1SRC", "W0SRC", "W1S"]:
        field.configure(uvm_reg(), 8, 16, acs, True, 0)
        field.field_lock()
        field.reset()
        local_rand_el = randint(1,(2**field.get_n_bits()-1))
        field.predict(local_rand_el, kind=uvm_predict_e.UVM_PREDICT_WRITE, path=uvm_door_e.UVM_FRONTDOOR)
        if field.get_access() in  ["W0S","W0SRC"]: ## anytime a bit is clear to 0 that bit is gonna be set to 1 if not already 1
            predicted_v = field.get_reset() | (~local_rand_el & int("".join(["1"]*field.get_n_bits()),2))
        elif field.get_access() in ["W1SRC","W1S"]: ## anytime a bit is set to 1 that bit is gonna be set to 1 if not already 1
            predicted_v = field.get_reset() | (local_rand_el & int("".join(["1"]*field.get_n_bits()),2))
        else:
            predicted_v = (2**field.get_n_bits()-1)
        assert field.get_value() == predicted_v, f"Failing for access {acs}"
        assert field.get_response() == uvm_resp_t.PASS_RESP, f"Failing as default status is not PASS_RESP is {field.get_response()}"

@pytest.mark.test_reg_field_field_predict_write_clear
def test_reg_field_field_predict_write_clear():
    from random import randint
    field = uvm_reg_field()
    ## With the clear register once we perfom the operation W the register will be cleared entirely according to the fields
    ## getting a prendicted value of 0 regardless of the predicted value we set through the function
    for acs in ["WOC","WC","W1C","W1CRS","W0C","W0CRS","WCRS"]:
        field.configure(uvm_reg(), 8, 16, acs, True, 0)
        field.field_lock()
        field.reset()
        local_rand_el = randint(1,(2**field.get_n_bits()-1))
        field.predict(local_rand_el, kind=uvm_predict_e.UVM_PREDICT_WRITE, path=uvm_door_e.UVM_FRONTDOOR)
        if field.get_access() in  ["W0C","W0CRC"]: ## anytime a bit is clear to 0 that bit is gonna be set to 0 if not already 0
            predicted_v = field.get_reset() & (local_rand_el & int("".join(["1"]*field.get_n_bits()),2))
        elif field.get_access() in ["W1CRC","W1C"]: ## anytime a bit is set to 1 that bit is gonna be set to 0 if not already 0
            predicted_v = field.get_reset() & (~local_rand_el & int("".join(["1"]*field.get_n_bits()),2))
        else:
            predicted_v = 0
        assert field.get_value() == predicted_v, "Failing for access {}".format(acs)
        assert field.get_response() == uvm_resp_t.PASS_RESP, "Failing as default status is not PASS_RESP is {}".format(field.get_response())

@pytest.mark.test_reg_field_field_predict_TOGGLE
def test_reg_field_field_predict_TOGGLE():
    from random import randint
    field = uvm_reg_field()
    ## With the clear register once we perfom the operation W the register will be cleared entirely according to the fields
    ## getting a prendicted value of 0 regardless of the predicted value we set through the function
    for acs in ["W1T","W0T"]:
        field.configure(uvm_reg(), 8, 16, acs, True, 0)
        field.field_lock()
        field.reset()
        local_rand_el = randint(1,(2**field.get_n_bits()-1))
        field.predict(local_rand_el, kind=uvm_predict_e.UVM_PREDICT_WRITE, path=uvm_door_e.UVM_FRONTDOOR)
        if "0" in field.get_access():   ## anytime a bit is cleared to 0 that bit is gonna be set to 1 or 0 toggling
            predicted_v = field.get_reset() ^ (~local_rand_el & int("".join(["1"]*field.get_n_bits()),2))
        else:                           ## anytime a bit is cleared to 1 that bit is gonna be set to 1 or 0 toggling
            predicted_v = field.get_reset() ^ (local_rand_el & int("".join(["1"]*field.get_n_bits()),2))
        assert field.get_value() == predicted_v, "Failing for access {}".format(acs)
        assert field.get_response() == uvm_resp_t.PASS_RESP, "Failing as default status is not PASS_RESP is {}".format(field.get_response())

@pytest.mark.test_reg_field_field_predict_NO_ACCESS
def test_reg_field_field_predict_NO_ACCESS():
    from random import randint
    field = uvm_reg_field()
    ## With the NO_ACCESS the reset value is always returned
    field.configure(uvm_reg(), 8, 16, "NO_ACCESS", True, randint(1,2**8-1))
    field.field_lock()
    field.reset()
    field.predict(randint(1,2**field.get_n_bits()), kind=uvm_predict_e.UVM_PREDICT_WRITE, path=uvm_door_e.UVM_FRONTDOOR)
    assert field.get_value() == field.get_reset(), "Failing for access NO_ACCESS"
    field.predict(randint(1,2**field.get_n_bits()), kind=uvm_predict_e.UVM_PREDICT_READ, path=uvm_door_e.UVM_FRONTDOOR)
    assert field.get_value() == field.get_reset(), "Failing for access NO_ACCESS"
    assert field.get_response() == uvm_resp_t.PASS_RESP, "Failing as default status is not PASS_RESP is {}".format(field.get_response())

@pytest.mark.test_reg_field_field_predict_status_error_on_write
def test_reg_field_field_predict_status_error_on_write():
    from random import randint
    field = uvm_reg_field()
    ## With the NO_ACCESS the reset value is always returned
    for acs in ["RO","RW","RC","RS"]:
        field.configure(uvm_reg(), 8, 16, acs, True, randint(1,2**8-1))
        field.field_lock()
        field.set_throw_error_on_read(True)
        field.set_throw_error_on_write(True)
        field.reset()
        field.predict(randint(1,2**field.get_n_bits()), kind=uvm_predict_e.UVM_PREDICT_WRITE, path=uvm_door_e.UVM_FRONTDOOR)
        assert field.get_response() == uvm_resp_t.ERROR_RESP, "Failing for access access: {} where UVM_READ is issued response is: {}".format(acs,field.get_response().name)

@pytest.mark.test_reg_field_field_predict_status_error_on_read
def test_reg_field_field_predict_status_error_on_read():
    from random import randint
    field = uvm_reg_field()
    # With the NO_ACCESS the reset value is always returned
    for acs in ["WO", "WOC", "WOS", "WO1", "NOACCESS", "W1", "W1T", "W0T", "WC", "WS", "W1C", "W1S", "W0C", "W0S"]:
        field.configure(uvm_reg(), 8, 16, acs, True, randint(1,2**8-1))
        field.field_lock()
        field.set_throw_error_on_read(True)
        field.set_throw_error_on_write(True)
        field.reset()
        field.predict(randint(1,2**field.get_n_bits()), kind=uvm_predict_e.UVM_PREDICT_READ, path=uvm_door_e.UVM_FRONTDOOR)
        assert field.get_response() == uvm_resp_t.ERROR_RESP, "Failing for access access: {} where UVM_READ is issued response is: {}".format(acs,field.get_response().name)