# Main Packages same as import uvm_pkg or uvm_defines.
from pyuvm import uvm_object
from pyuvm.error_classes import UVMFatalError
from pyuvm.s17_uvm_reg_enumerations import *
from pyuvm.s24_uvm_reg_includes import *
from pyuvm.s20_uvm_reg import uvm_reg


# Class declaration for register field
# @rand_enable(enable_pyvsc)


class uvm_reg_field(uvm_object):
    # constructor
    def __init__(self, name='uvm_reg_field'):
        super().__init__(name)
        self.access_list = uvm_reg_policy_t
        self._parent = None
        self._size = 0
        self._lsb_pos = None
        self._access = ""  # Start with empty access
        self._err_list = []
        self._is_volatile = False
        self._reset = 0
        self._field_mirrored = 0
        self._value = 0
        # Keep desired value as random
        if enable_pyvsc is True:
            pass
            # self._desidered = vsc.rand_bit_t(self._size)
        else:
            self._desidered = 0
        self._config_done = False
        self._has_been_writ = False
        self._prediction = predict_t
        self._response = uvm_resp_t
        self._name = name
        self._header = name + " -- "
        # These 2 flags cannot change for fields since
        # they are part of the parent register
        self._error_on_read = False
        self._error_on_write = False

    # configure
    def configure(self,
                  parent: uvm_reg,
                  size: int,
                  lsb_pos: int,
                  access: str,
                  is_volatile: bool,
                  reset: int):
        self._parent = parent
        self._size = size
        self._lsb_pos = lsb_pos
        self._access = access
        self._is_volatile = is_volatile
        self._reset = reset
        self._config_done = False
        self._compare = check_t
        # Additional Checking
        # Ignore randomization if the field is known not to be writeable
        # i.e. not "RW", "WRC", "WRS", "WO", "W1", "WO1"
        if enable_pyvsc is True:
            if self._access in ["RW", "WRC", "WRS", "WO", "W1", "WO1"]:
                self._desidered.rand_mode = True
            else:
                self._desidered.rand_mode = False
        else:
            self._desidered = 0
        # Check if size is 0
        if (self._size == 0):
            raise UVMFatalError(f"""{self._header} Size
                of a filed cannot be 0 MINIMUN allowed is 1""")
        # Check if policy is a valid policy
        if (self._access not in self.access_list):
            self._access = "NOACCESS"
        # These 2 flags cannot change for fields since are part
        # of the parent register
        self._error_on_read = self._parent.throw_error_on_read
        self._error_on_write = self._parent.throw_error_on_write
        # one configure is called let's unlock
        self.field_unlock()
        # check the reset value is not beyond the MAX
        if (self._reset >= (2**self._size)):
            error_out(self._header, f"""Reset value for feild : {self._name}
                is [{self._reset}] is beyond the MAX valoue given by
                the size [{((2**self._size)-1)}]""")
        # Add field
        parent._add_field(self)

    # lock method meaning the configursation is done
    # and we can unlock all the internal methods
    def field_lock(self):
        self._config_done = True

    def field_unlock(self):
        self._config_done = False

    # adding error to the main error list
    def _add_error(self, value):
        self._err_list.append(value)

    # checking mechanims for error list
    def _check_(self):
        if (len(self._err_list) > 0):
            (print(self._err_list[el] for el in range(len(self._err_list))))

    # set_compare
    def set_compare(self, check_type: check_t):
        self._check = check_type

    # set_throw_error_on_read
    def set_throw_error_on_read(self, teor=False):
        self._error_on_read = teor

    # set_throw_error_on_write
    def set_throw_error_on_write(self, teow=False):
        self._error_on_write = teow

    # get_compare
    def get_compare(self):
        return self._check

    # get_full_name
    def get_full_name(self):
        return self._parent + "." + self._name

    # get_name
    def get_name(self):
        return self._name

    # Common method to check if uvm_reg_field is configured
    # if configured return the pass_value else return fail value
    # after updating error list
    def _check_if_configured_and_execute(self, pass_value, fail_value):
        if self._config_done is False:
            error_out(self._header, "Configure for a field must be called"
                                    "called before any other memeber method")
            self._add_error(
                uvm_reg_field_error_decoder.CONFIGURE_MUST_BE_CALLED_BEFORE)
            return fail_value
        else:
            return pass_value

    # get_parent
    def get_parent(self):
        return self._check_if_configured_and_execute(self._parent, None)

    # get_lsb_pos
    def get_lsb_pos(self) -> int:
        return self._check_if_configured_and_execute(self._lsb_pos, 0)

    # get_msb_pos
    def get_msb_pos(self) -> int:
        msb_pos = self.get_lsb_pos() + self.get_n_bits() - 1
        return self._check_if_configured_and_execute(msb_pos, 0)

    # get_n_bits
    def get_n_bits(self) -> int:
        return self._check_if_configured_and_execute(self._size, 0)

    # get_access
    def get_access(self) -> str:
        return self._check_if_configured_and_execute(self._access, "")

    # is_known_access
    def is_known_access(self) -> bool:
        return self._access in self.access_list

    # is_volatile
    def is_volatile(self) -> bool:
        return self._check_if_configured_and_execute(self._is_volatile, False)

    # get_reset
    def get_reset(self) -> int:
        return self._check_if_configured_and_execute(self._reset, 0)

    # atomic get value
    def get(self):
        return self._desidered

    # atomic reset value
    def reset(self):
        self._field_mirrored = self._reset
        self._has_been_writ = False
        self._response = uvm_resp_t.PASS_RESP

    # atomic get value
    def get_value(self):
        return self._field_mirrored

    # Atomic set access value
    def set_access(self, access_value):
        if (not isinstance(access_value, str)):
            error_out(self._header, "Access set for field must be a string")
            self._add_error(
                uvm_reg_field_error_decoder.ACCESS_TYPE_NEEDS_TO_BE_A_STRING)
        else:
            if (access_value is self.access_list):
                self._access = access_value
            else:
                error_out(self._header, "Access value provided is not"
                                        "part of possible access values")
                self._add_error(
                    uvm_reg_field_error_decoder.ACCESS_VALUE_OUT_OF_LIST)
                self._access = "NOACCESS"

    # Atomic set response status for fields
    def set_response(self, f_response: uvm_resp_t):
        self._response = f_response

    # Atomic set prediction type for field. This comes from the register parent
    def set_prediction(self, pred_type: predict_t):
        self._prediction = pred_type

    # Atomic get status from fields
    def get_response(self):
        return self._response

    # atomic set value
    def field_set(self, value: int):
        # Define an all 1 values
        _mask = int("".join(["1"] * self._size), 2)
        # check if value given is bigger than the size of field

        # Ideally the set value should be checked against the
        # parent register being accessed.
        # Not yet implemenmted
        # if the parent is under WRITE there should be no set called.

        # Return value based on the access
        if self.get_access() == "RO":
            pass  # Leave the desired value stable
        if self.get_access() == "RW":
            self._desidered = value
        if self.get_access() == "RC":
            pass  # Leave the desired value stable
        if self.get_access() == "RS":
            pass  # Leave the desired value stable
        if self.get_access() == "WC":
            self._desidered = 0
        if self.get_access() == "WS":
            self._desidered = _mask
        if self.get_access() == "WRC":
            self._desidered = value
        if self.get_access() == "WRS":
            self._desidered = value
        if self.get_access() == "WSRC":
            self._desidered = _mask
        if self.get_access() == "WCRS":
            self._desidered = 0
        if self.get_access() == "W1C":
            self._desidered = self._desidered & (~value)
        if self.get_access() == "W1S":
            self._desidered = self._desidered | value
        if self.get_access() == "W1T":
            self._desidered = self._desidered ^ value
        if self.get_access() == "W0C":
            self._desidered = self._desidered & value
        if self.get_access() == "W0S":
            self._desidered = self._desidered | (~value & _mask)
        if self.get_access() == "W0T":
            self._desidered = self._desidered ^ (~value & _mask)
        if self.get_access() == "W1SRC":
            self._desidered = self._desidered | value
        if self.get_access() == "W1CRS":
            self._desidered = self._desidered & (~value)
        if self.get_access() == "W0SRC":
            self._desidered = self._desidered | (~value & _mask)
        if self.get_access() == "W0CRS":
            self._desidered = self._desidered & value
        if self.get_access() == "WO":
            self._desidered = value
        if self.get_access() == "WOC":
            self._desidered = 0
        if self.get_access() == "WOS":
            self._desidered = _mask
        if self.get_access() == "W1":
            if self._has_been_writ is True:
                pass  # Leave the desired value stable
            else:
                self._desidered = value
        if self.get_access() == "WO1":
            if self._has_been_writ is True:
                pass  # Leave the desired value stable
            else:
                self._desidered = value
        if self.get_access() == "NOACCESS":
            pass  # Leave the desired value stable

    # Since there is no Switch case in python we use a simple switch case
    # Where error is mentioned it depends on _error_on_write flag, no effect
    # will be translated in Error reponse if flag is enable
    # "RO"       - W: no effect, R: no effect
    # "RW"       - W: as-is, R: no effect
    # "RC"       - W: no effect, R: clears all bits
    # "RS"       - W: no effect, R: sets all bits
    # "WRC"      - W: as-is, R: clears all bits
    # "WRS"      - W: as-is, R: sets all bits
    # "WC"       - W: clears all bits, R: no effect
    # "WS"       - W: sets all bits, R: no effect
    # "WSRC"     - W: sets all bits, R: clears all bits
    # "WCRS"     - W: clears all bits, R: sets all bits
    # "W1C"      - W: 1/0 clears/no effect on matching bit, R: no effect
    # "W1S"      - W: 1/0 sets/no effect on matching bit, R: no effect
    # "W1T"      - W: 1/0 toggles/no effect on matching bit, R: no effect
    # "W0C"      - W: 1/0 no effect on/clears matching bit, R: no effect
    # "W0S"      - W: 1/0 no effect on/sets matching bit, R: no effect
    # "W0T"      - W: 1/0 no effect on/toggles matching bit, R: no effect
    # "W1SRC"    - W: 1/0 sets/no effect on matching bit, R: clears all bits
    # "W1CRS"    - W: 1/0 clears/no effect on matching bit, R: sets all bits
    # "W0SRC"    - W: 1/0 no effect on/sets matching bit, R: clears all bits
    # "W0CRS"    - W: 1/0 no effect on/clears matching bit, R: sets all bits
    # "WO"       - W: as-is, R: error
    # "WOC"      - W: clears all bits, R: error
    # "WOS"      - W: sets all bits, R: error
    # "W1"       - W: first one after ~HARD~ reset is as-is,
    #                 other W have no effects, R: no effect
    # "WO1"      - W: first one after ~HARD~ reset is as-is,
    #                 other W have no effects, R: error
    # "NOACCESS" - W: no effect, R: no effect
    def predict_based_on_write(self, wr_val):
        # Define an all 1 values
        _mask = int("".join(["1"] * self._size), 2)
        # Return value based on the access type
        if self.get_access() == "RO":
            self._field_mirrored = self._reset
        if self.get_access() == "RW":
            self._field_mirrored = wr_val
        if self.get_access() == "RC":
            self._field_mirrored = self._field_mirrored
        if self.get_access() == "RS":
            self._field_mirrored = self._field_mirrored
        if self.get_access() == "WC":
            self._field_mirrored = 0
        if self.get_access() == "WS":
            self._field_mirrored = _mask
        if self.get_access() == "WRC":
            self._field_mirrored = wr_val
        if self.get_access() == "WRS":
            self._field_mirrored = wr_val
        if self.get_access() == "WSRC":
            self._field_mirrored = _mask
        if self.get_access() == "WCRS":
            self._field_mirrored = 0
        if self.get_access() == "W1C":
            self._field_mirrored = self._field_mirrored & (~wr_val)
        if self.get_access() == "W1S":
            self._field_mirrored = self._field_mirrored | wr_val
        if self.get_access() == "W1T":
            self._field_mirrored = self._field_mirrored ^ wr_val
        if self.get_access() == "W0C":
            self._field_mirrored = self._field_mirrored & wr_val
        if self.get_access() == "W0S":
            self._field_mirrored = self._field_mirrored | (~wr_val & _mask)
        if self.get_access() == "W0T":
            self._field_mirrored = self._field_mirrored ^ (~wr_val & _mask)
        if self.get_access() == "W1SRC":
            self._field_mirrored = self._field_mirrored | wr_val
        if self.get_access() == "W1CRS":
            self._field_mirrored = self._field_mirrored & (~wr_val)
        if self.get_access() == "W0SRC":
            self._field_mirrored = self._field_mirrored | (~wr_val & _mask)
        if self.get_access() == "W0CRS":
            self._field_mirrored = self._field_mirrored & wr_val
        if self.get_access() == "WO":
            self._field_mirrored = wr_val
        if self.get_access() == "WOC":
            self._field_mirrored = 0
        if self.get_access() == "WOS":
            self._field_mirrored = _mask
        if self.get_access() == "W1":
            if self._has_been_writ is True:
                self._field_mirrored = self._field_mirrored
            else:
                self._field_mirrored = wr_val
        if self.get_access() == "WO1":
            if self._has_been_writ is True:
                self._field_mirrored = self._field_mirrored
            else:
                self._field_mirrored = wr_val
        if self.get_access() == "NOACCESS":
            self._field_mirrored = self._reset

    # atomic predict value based on the operation (READ)
    # Where error is mentioned it depends on _error_on_read flag, no effect
    # will be translated in Error reponse if flag is enable
    # Since there is no Switch case in python we use a simple switch case
    # "RO"       - W: no effect, R: return the mirrored value (reset one)
    # "RW"       - W: as-is, R: as-is
    # "RC"       - W: no effect, R: clears all bits
    # "RS"       - W: no effect, R: sets all bits
    # "WRC"      - W: as-is, R: clears all bits
    # "WRS"      - W: as-is, R: sets all bits
    # "WC"       - W: clears all bits, R: no effect
    # "WS"       - W: sets all bits, R: no effect
    # "WSRC"     - W: sets all bits, R: clears all bits
    # "WCRS"     - W: clears all bits, R: sets all bits
    # "W1C"      - W: 1/0 clears/no effect on matching bit, R: no effect
    # "W1S"      - W: 1/0 sets/no effect on matching bit, R: no effect
    # "W1T"      - W: 1/0 toggles/no effect on matching bit, R: no effect
    # "W0C"      - W: 1/0 no effect on/clears matching bit, R: no effect
    # "W0S"      - W: 1/0 no effect on/sets matching bit, R: no effect
    # "W0T"      - W: 1/0 no effect on/toggles matching bit, R: no effect
    # "W1SRC"    - W: 1/0 sets/no effect on matching bit, R: clears all bits
    # "W1CRS"    - W: 1/0 clears/no effect on matching bit, R: sets all bits
    # "W0SRC"    - W: 1/0 no effect on/sets matching bit, R: clears all bits
    # "W0CRS"    - W: 1/0 no effect on/clears matching bit, R: sets all bits
    # "WO"       - W: as-is, R: error
    # "WOC"      - W: clears all bits, R: error
    # "WOS"      - W: sets all bits, R: error
    # "W1"       - W: first one after ~HARD~ reset is as-is,
    #                 other W have no effects, R: no effect
    # "WO1"      - W: first one after ~HARD~ reset is as-is,
    #                 other W have no effects, R: error
    # "NOACCESS" - W: no effect, R: no effect
    def predict_based_on_read(self, value):
        # FRONTDOOR
        if self.get_access() in ["RC", "WRC", "WSRC", "W1SRC", "W0SRC"]:
            # Set Value to 0 since READ will clear
            self._field_mirrored = 0
        elif self.get_access() in ["RS", "WRS", "WCRS", "W1CRS", "W0CRS"]:
            # Set Value to 1 since READ will set to 1
            self._field_mirrored = int("".join(["1"] * self._size), 2)
        elif self.get_access() in ["WO", "WOC", "WOS", "WO1", "NOACCESS",
                                   "W1", "W1T", "W0T", "WC", "WS", "W1C",
                                   "W1S", "W0C", "W0S"]:
            # Set Value to the reset since READ will have no effect
            self._field_mirrored = self._reset
        else:
            self._add_error(
                uvm_reg_field_error_decoder.WRONG_ACCESS_FOR_PREDICT_READ)
            error_out(self._header,
                      "Wrong Access set on predict_based_on_read")

    # Check the Direction and the access type along with the enable error
    # flags (if error is supposed to be thown then send it out)
    def predict_response(self, value, path: path_t, direction: access_e):
        # Check the Direction and the access type along with
        # the enable error flags (if error is supposed to be
        # thrown then send it out)
        # if we try to write a 1 when the access on write will
        # require the 0 to generate some effect
        response = uvm_resp_t.PASS_RESP
        write_error_accesses = ["RO", "RW", "RC", "RS"]
        read_error_accesses = ["WO", "WOC", "WOS", "WO1",
                               "NOACCESS", "W1", "W1T",
                               "W0T", "WC", "WS", "W1C",
                               "W1S", "W0C", "W0S"]
        if path == path_t.FRONTDOOR:
            if (direction == access_e.PYUVM_WRITE) and \
                (self.get_access() in write_error_accesses) and \
                    (self._error_on_write is True):
                response = uvm_resp_t.ERROR_RESP
            elif (direction == access_e.PYUVM_READ) and \
                 (self.get_access() in read_error_accesses) and \
                    (self._error_on_read is True):
                response = uvm_resp_t.ERROR_RESP

        else:  # This will include the BACKDOOR
            pass  # default value set above
        self.set_response(response)

    # Main field prediction function to be used to predict
    # mirrored value for uvm_fields
    def field_predict(self, value, path: path_t, direction: access_e):
        # Predict the status based on the flags
        self.predict_response(value, path, direction)
        # WRITE prediction and prediction is ether on write and Direct
        if (direction == access_e.PYUVM_WRITE) and \
            (path == path_t.FRONTDOOR) and \
                (self._prediction in [predict_t.PREDICT_DIRECT,
                                      predict_t.PREDICT_WRITE]):
            self.predict_based_on_write(value)
        # READ prediction and prediction is ether on read and Direct
        elif (direction == access_e.PYUVM_READ) and \
             (path == path_t.FRONTDOOR) and \
                (self._prediction in [predict_t.PREDICT_DIRECT,
                                      predict_t.PREDICT_READ]):
            self.predict_based_on_read(value)
        elif (path == path_t.BACKDOOR):
            self._field_mirrored = value
            self.set_response(uvm_resp_t.PASS_RESP)
        else:
            self._add_error(
                uvm_reg_field_error_decoder.
                WRONG_COMBINATION_PREDICTION_DIRECTION)
            error_out(self._header,
                      "Wrong combination of PATH - PREDICTION TYPE "
                      "and DIRECTION on uvm_field -- "
                      "field_predict function")

    # String representation of uvm_reg_filed class content
    def __str__(self) -> str:
        return f"   {self._header} \
                    parent :    {self._parent} \
                    size:       {self._size} \
                    lsb_pos:    {self._lsb_pos} \
                    access:     {self._access} \
                    error:      {self._err_list} \
                    is_volatile:{self._is_volatile} \
                    reset:      {self._reset} \
                    mirrored:   {self._field_mirrored} \
                    value:      {self._value}"

    ############################################
    # Yet to be implemeneted
    ############################################
    '''
        1. Checking the set during a write happening on the Parent register
        2. Checking if the write or read operation is ongoing
        3. implement any reference needed for the BACKDOOR
        4. implement the single field write method (should take the UVM_REG
           parent as reference)
    '''
