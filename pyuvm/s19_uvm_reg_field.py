# Main Packages same as import uvm_pkg or uvm_defines.
from pyuvm import uvm_object
from pyuvm.s17_uvm_reg_enumerations import uvm_reg_policy_t, uvm_reg_byte_en_t
from pyuvm.s17_uvm_reg_enumerations import uvm_predict_e, uvm_door_e
from pyuvm.s17_uvm_reg_enumerations import uvm_status_e, uvm_reg_data_t
from pyuvm.s20_uvm_reg import uvm_reg
from pyuvm.s21_uvm_reg_map import uvm_reg_map
from pyuvm.s23_uvm_reg_item import uvm_reg_item
from pyuvm.s24_uvm_reg_includes import uvm_resp_t, path_t
from pyuvm.s24_uvm_reg_includes import check_t, uvm_fatal
from pyuvm.s24_uvm_reg_includes import error_out, access_e
from pyuvm.s24_uvm_reg_includes import uvm_error, uvm_reg_field_error_decoder
from typing import Tuple

############################################
# Yet to be implemeneted TODO:
############################################
'''
    1.  Checking the set during a write happening on the Parent register
    2.  Checking if the write or read operation is ongoing
    3.  implement any reference needed for the BACKDOOR
    4.  implement the single field write method (should take the UVM_REG parent
        as reference)
'''


# Class declaration for register field
class uvm_reg_field(uvm_object):
    # constructor
    def __init__(self, name='uvm_reg_field'):
        super().__init__(name)
        self.access_list = uvm_reg_policy_t
        self._parent = None
        self._size = 0
        self._lsb_pos = None
        # Start with empty access
        self._access = ""
        self._err_list = []
        self._is_volatile = False
        self._reset = 0
        self._field_mirrored = 0
        self._value = 0
        # Keep desired value as 0
        # TODO: add eventually support for PYVSC for randomization
        self._desired = 0
        self._config_done = False
        self._has_been_writ = False
        self._response = uvm_resp_t
        self._header = name + " -- "
        # These 2 flags cannot change for fields
        # since are part of the parent register
        self._error_on_read = False
        self._error_on_write = False
        self._fname = ""
        self._lineno = 0

    # configure
    def configure(self, parent: uvm_reg, size: int, lsb_pos: int, access: str,
                  is_volatile: bool, reset: int):
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
        # TODO: add eventually support for PYVSC for randomization
        self._desired = 0
        # Check if size is 0
        if (self._size == 0):
            uvm_fatal(self._header, "Size of a filed \
                      cannot be 0 MINIMUN allowed is 1")
        # Check if policy is a valid policy
        if (self._access not in self.access_list):
            self._access = "NOACCESS"
        # These 2 flags cannot
        # change for fields since are part of the parent register
        self._error_on_read = self._parent.throw_error_on_read
        self._error_on_write = self._parent.throw_error_on_write
        # one configure is called let's lock
        self.field_lock()
        # check the reset value is not beyond the MAX
        if (self._reset >= (2**self._size)):
            uvm_error(self._header, f"Reset value for REG \
                      feild : {self.get_name()} is [{self._reset}] \
                      is beyond the MAX valoue given \
                      by the size [{((2**self._size) - 1)}]")
        # Add field
        parent._add_field(self)

    # lock method meaning the configursation is
    # done and we can unlock all the internal methods
    def field_lock(self):
        self._config_done = True

    # field_unlock
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
        return self._parent.get_full_name() + "." + self.get_name()

    # get_parent
    def get_parent(self):
        if self._config_done is False:
            error_out(self._header, "Configure for a \
                      field must be called called \
                      before any other memeber method")
            self._add_error(
                uvm_reg_field_error_decoder.CONFIGURE_MUST_BE_CALLED_BEFORE)
            return None
        else:
            return self._parent

    # get_lsb_pos
    def get_lsb_pos(self) -> int:
        if self._config_done is False:
            error_out(self._header, "Configure for a \
                      field must be called called \
                      before any other memeber method")
            self._add_error(
                uvm_reg_field_error_decoder.CONFIGURE_MUST_BE_CALLED_BEFORE)
            return 0
        else:
            return self._lsb_pos

    # get_msb_pos
    def get_msb_pos(self) -> int:
        if self._config_done is False:
            error_out(self._header, "Configure for a \
                      field must be called called before\
                       any other memeber method")
            self._add_error(
                uvm_reg_field_error_decoder.CONFIGURE_MUST_BE_CALLED_BEFORE)
            return 0
        else:
            return self.get_lsb_pos() + self.get_n_bits() - 1

    # get_n_bits
    def get_n_bits(self) -> int:
        if self._config_done is False:
            error_out(self._header, "Configure for a field must \
                      be called called before any other memeber method")
            self._add_error(
                uvm_reg_field_error_decoder.CONFIGURE_MUST_BE_CALLED_BEFORE)
            return 0
        else:
            return self._size

    # get_access
    def get_access(self) -> str:
        if self._config_done is False:
            error_out(self._header, "Configure for a field \
                      must be called called before any other memeber method")
            self._add_error(
                uvm_reg_field_error_decoder.CONFIGURE_MUST_BE_CALLED_BEFORE)
            return ""
        else:
            return self._access

    # is_known_access
    def is_known_access(self) -> bool:
        return self._access in self.access_list

    # is_volatile
    def is_volatile(self) -> bool:
        if self._config_done is False:
            error_out(self._header, "Configure for\
                       a field must be called called \
                      before any other memeber method")
            return False
        else:
            return self._is_volatile

    # get_reset
    def get_reset(self) -> int:
        if self._config_done is False:
            error_out(self._header, "Configure for a \
                      field must be called called before \
                      any other memeber method")
            self._add_error(
                uvm_reg_field_error_decoder.CONFIGURE_MUST_BE_CALLED_BEFORE)
            return 0
        else:
            return self._reset

    # atomic get value
    def get(self):
        return self._desired

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
            error_out(self._header, "Access set for reg \
                      field needs to be a string")
            self._add_error(
                uvm_reg_field_error_decoder.ACCESS_TYPE_NEEDS_TO_BE_A_STRING)
        else:
            if (access_value is self.access_list):
                self._access = access_value
            else:
                error_out(self._header, "Access value \
                          provided is not part of possible access values")
                self._add_error(
                    uvm_reg_field_error_decoder.ACCESS_VALUE_OUT_OF_LIST)
                self._access = "NOACCESS"

    # Atomic set response status for fields
    def set_response(self, f_response: uvm_resp_t):
        self._response = f_response

    # Atomic get status from fields
    def get_response(self):
        return self._response

    # atomic set value
    def field_set(self, value: int):
        # Define an all 1 values
        _mask = (1 << self._size) - 1
        # check if value given is bigger than the size of field

        # Ideally the set value should be checked against the parent
        # register being accessed.
        # if the parent is under WRITE there should be no set called.
        # Not yet implemenmted.
        #
        #

        field_access = self.get_access()
        # Return value based on the access
        if field_access in ("RO", "RC", "RS", "NOACCESS"):
            self._desired = self._desired  # Leave the desired value stable
        elif field_access in ("RW", "WRC", "WRS", "WO"):
            self._desired = value
        elif field_access in ("WC", "WCRS", "WOC"):
            self._desired = 0
        elif field_access in ("WS", "WSRC", "WOS"):
            self._desired = _mask
        elif field_access in ("W1C", "W1CRS"):
            self._desired = self._desired & (~value)
        elif field_access in ("W1S", "W1SRC"):
            self._desired = self._desired | value
        elif field_access == "W1T":
            self._desired = self._desired ^ value
        elif field_access in ("W0C", "W0CRS"):
            self._desired = self._desired & value
        elif field_access in ("W0S", "W0SRC"):
            self._desired = self._desired | (~value & _mask)
        elif field_access == "W0T":
            self._desired = self._desired ^ (~value & _mask)
        elif field_access in ("W1", "WO1"):
            if self._has_been_writ is False:
                self._desired = value
        else:
            self._desired = value

    # Check the Direction and the access type along with the enable error
    # flags (if error is supposed to be thown then send it out)
    def predict_response(self, path: path_t, direction: access_e):
        # Check the Direction and the access type along with the enable error
        # flags (if error is supposed to be thown then send it out)
        # if we try to write a 1 when the access on write will require the 0
        # to generate some effect
        if ((direction == uvm_predict_e.UVM_PREDICT_WRITE) & (
                self.get_access() in ["RO", "RW", "RC", "RS"]) & (
                    path == uvm_door_e.UVM_FRONTDOOR)):
            self.set_response(uvm_resp_t.PASS_RESP if (
                self._error_on_write is False) else uvm_resp_t.ERROR_RESP)
        elif ((direction == uvm_predict_e.UVM_PREDICT_READ) & (
                self.get_access() in ["WO", "WOC", "WOS", "WO1",
                                      "NOACCESS", "W1", "W1T",
                                      "W0T", "WC", "WS", "W1C",
                                      "W1S",
                                      "W0C",
                                      "W0S"]) & (
                                          path == uvm_door_e.UVM_FRONTDOOR)):
            self.set_response(uvm_resp_t.PASS_RESP if (
                self._error_on_read is False) else uvm_resp_t.ERROR_RESP)
        else:  # This will include the BACKDOOR
            self.set_response(uvm_resp_t.PASS_RESP)

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
    def predict_write(self, cur_val, wr_val) -> int:
        # Define an all 1 values
        mask = (1 << self._size) - 1
        # Return value based on the access type
        field_access = self.get_access()
        if field_access in ("RO", "RC", "RS", "NOACCESS"):
            return cur_val
        elif field_access in ("RW", "WRC", "WRS", "WO"):
            return wr_val
        elif field_access in ("WC", "WCRS", "WOC"):
            return 0
        elif field_access in ("WS", "WSRC", "WOS"):
            return mask
        elif field_access in ("W1C", "W1CRS"):
            return cur_val & (~wr_val)
        elif field_access in ("W1S", "W1SRC"):
            return cur_val | wr_val
        elif field_access in ("W1T"):
            return cur_val ^ wr_val
        elif field_access in ("W0C", "W0CRS"):
            return cur_val & wr_val
        elif field_access in ("W0S", "W0SRC"):
            return cur_val | (~wr_val & mask)
        elif field_access in ("W0T"):
            return cur_val ^ (~wr_val & mask)
        elif field_access in ("W1", "WO1"):
            if self._has_been_writ:
                return cur_val
            else:
                return wr_val
        else:
            return wr_val

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
    # "W1"       - W: first one after ~HARD~ reset is as-is, other W have no
    #                 effects, R: no effect
    # "WO1"      - W: first one after ~HARD~ reset is as-is, other W have no
    #                 effects, R: error
    # "NOACCESS" - W: no effect, R: no effect
    def predict_read(self) -> Tuple[bool, int]:
        acc: str = self.get_access()
        if acc in ["RC", "WRC", "WSRC", "W1SRC", "W0SRC"]:
            # Set Value to 0 since READ will clear
            return True, 0
        elif acc in ["RS", "WRS", "WCRS", "W1CRS", "W0CRS"]:
            # Set Value to 1 since READ will set to 1
            return True, (1 << self._size) - 1
        elif acc in ["WO", "WOC", "WOS", "WO1", "NOACCESS",
                     "W1", "W1T", "W0T", "WC", "WS", "W1C",
                     "W1S", "W0C", "W0S"]:
            # Set Value to the reset since READ will have no effect
            return True, self._reset
        return False, 0

    # Proccess of predictiong
    def do_predict(self,
                   rw: uvm_reg_item,
                   kind: uvm_predict_e = uvm_predict_e.UVM_PREDICT_DIRECT,
                   be: uvm_reg_byte_en_t = -1):
        field_val = rw.get_value(0) & ((1 << self._size) - 1)

        self.predict_response(rw.get_door(), kind)

        if rw.get_status() != uvm_status_e.UVM_NOT_OK:
            rw.set_status(uvm_status_e.UVM_IS_OK)

        if not be & 0b1:
            return

        self._fname = rw.get_fname()
        self._lineno = rw.get_line()

        if kind == uvm_predict_e.UVM_PREDICT_WRITE:
            if rw.get_door() == uvm_door_e.UVM_FRONTDOOR \
                    or rw.get_door() == uvm_door_e.UVM_PREDICT:
                field_val = self.predict_write(self._field_mirrored, field_val)
            self._has_been_writ = True
            # here need to do uvm_reg_field_cb_iter logic
            field_val &= (1 << self._size) - 1
        elif kind == uvm_predict_e.UVM_PREDICT_READ:
            if rw.get_door() == uvm_door_e.UVM_FRONTDOOR \
                    or rw.get_door() == uvm_door_e.UVM_PREDICT:
                predict_valid, tmp_val = self.predict_read()
                if predict_valid:
                    field_val = tmp_val
            # here need to do uvm_reg_field_cb_iter logic
            field_val &= (1 << self._size) - 1
        elif kind == uvm_predict_e.UVM_PREDICT_DIRECT:
            # There should be a check for the register's busy status,
            # but since there is no 'busy' field in the register class,
            # there is no such check here.
            pass
        else:
            self._add_error(uvm_reg_field_error_decoder.
                            WRONG_COMBINATION_PREDICTION_DIRECTION)
            uvm_error(self._header, "Wrong combination of PATH \
                       - PREDICTION TYPE and DIRECTION on pyuvm_field \
                       -- field_predict function")
        self._field_mirrored = field_val
        self._desired = field_val
        self._value = field_val

    # Main field prediction function to be used to predict
    # mirrored value for pyuvm_fields
    # 18.5.5.17
    def predict(self,
                value: uvm_reg_data_t,
                be: uvm_reg_byte_en_t = -1,
                kind: uvm_predict_e = uvm_predict_e.UVM_PREDICT_DIRECT,
                path: uvm_door_e = uvm_door_e.UVM_FRONTDOOR,
                map: uvm_reg_map = None,
                fname: str = "",
                lineno: int = 0) -> bool:

        rw = uvm_reg_item()
        rw.set_value(value)
        rw.set_door(path)
        rw.set_map(map)
        rw.set_fname(fname)
        rw.set_line(lineno)
        self.do_predict(rw, kind, be)
        if rw.get_status() == uvm_status_e.UVM_NOT_OK:
            return False
        return True

    # String representation of pyuvm_reg_filed class content
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
