# Main Packages same as import uvm_pkg or uvm_defines.svh
from pyuvm import uvm_object
from pyuvm.s21_uvm_reg_map import uvm_reg_map
from pyuvm.s24_uvm_reg_includes import uvm_reg_error_decoder, error_out
from pyuvm.s24_uvm_reg_includes import access_e, path_t, uvm_fatal
from pyuvm.s24_uvm_reg_includes import uvm_not_implemeneted
from pyuvm.s24_uvm_reg_includes import uvm_resp_t, check_t, predict_t


# Class declaration
class uvm_reg(uvm_object):
    # Constructor
    def __init__(self, name="uvm_reg", reg_width=32):
        super().__init__(name)
        self._parent = None
        self._fields = []
        self._err_list = []
        self._mirrored = 0
        self._desired = 0
        self._reset = 0
        self._sum = 0
        self._name = name
        self._header = name + " -- "
        self._address = "0x0"
        self._path = ""
        self._width = reg_width
        # If set those 2 flags will override fields values, and if set to True
        # the fields will report error reponse
        # in case of (Operation,Access) expect an error
        self.throw_error_on_read = False
        self.throw_error_on_write = False
        # Internal varibales used to detect if an operation is in progress
        # there were will be no difference between read and write
        # we cannot read and write from to the same register at tsame time
        self._op_in_progress = False
        self._is_cover_ion = False
        self._cover_on = False

    # configure
    def configure(self, parent, address, hdl_path,
                  throw_error_on_read=False,
                  throw_error_on_write=False):
        self._parent = parent
        self._address = address
        self._path = hdl_path
        self._sum = 0
        # If set those 2 flags will override fields values,
        # and if set to True the fields will report error reponse
        # in case of (Operation,Access) expect an error
        self.throw_error_on_read = throw_error_on_read
        self.throw_error_on_write = throw_error_on_write
        # Call the build function before adding any register to the main BLOCK
        self.build()
        # TODO: Check if the lock for the above register is set
        # TODO: Add a reference to the parent MAP
        # TODO: Add register to the Master Reg Block
        parent._add_register(self)

    # adding error to the main error list
    def _add_error(self, value):
        self._err_list.append(value)

    # create a message
    def gen_message(self, mss: str) -> str:
        return self._header + mss

    # checking mechanims for error list
    def check_err_list(self):
        if (len(self._err_list) > 0):
            for el in range(len(self._err_list)):
                print("List has error[{}]: {}".format(el, self._err_list[el]))
        else:
            print("No error in list")

    # get parent
    def get_parent(self):
        return self._parent

    # get_fields Return fields in canonical order (LSB to MSB)
    def get_fields(self):
        return self._fields

    # get size function
    def get_reg_size(self) -> int:
        if (self._width == 0):
            error_out(self._header, "_width cannot be 0")
            self._add_error(uvm_reg_error_decoder.REG_SIZE_CANNOT_BE_ZERO.name)
            return 0
        else:
            return self._width

    # setting the desired value, if this one is set we can
    # avoid using the Value in write
    def set_desired(self, value):
        for f in self._fields:
            f.field_set((value >> f.get_lsb_pos()))

    # _add_field
    def _add_field(self, field):
        # - field not None
        if (field is None):
            error_out(self._header, "_add_field Fields cannot be None")
            self._add_error(uvm_reg_error_decoder.FIELD_CANNOT_BE_NONE.name)
        # - field not already added
        if (field in self._fields):
            error_out(self._header, f"_add_field: Fields {field.get_name()} \
                      is already added")
            self._add_error(uvm_reg_error_decoder.FIELD_ALREADY_ADDED.name)
        # - if we did not error out we can append the field to the list
        self._fields.append(field)
        # - field fits in reg
        self._sum += field.get_n_bits()
        if (self._width < self._sum):
            error_out(self._header, f"_add_field: Fields {field.get_name()} \
                      doesn't fit into a {self._width} bits register")
            self._add_error(
                uvm_reg_error_decoder.FIELD_DOESNT_FIT_INTO_REG.name)
        # - field doesn't overlap with any other field
        if (len(self._fields) > 1):
            msb_pos = self._fields[self._fields.index(field) - 1].get_msb_pos()
            if (field.get_lsb_pos() - msb_pos <= 0):
                error_out(self._header, f"_add_field: \
                Fields {field.get_name()} overlap \
                with field \
                {self._fields[self._fields.index(field)-1].get_name()}")
                self._add_error(
                    uvm_reg_error_decoder.FIELD_OVERLAPPING_ERROR.name)

    # _set_lock
    def _set_lock(self):
        for _f in self._fields:
            _f.field_lock()

    # _set_unlock
    def _set_unlock(self):
        for _f in self._fields:
            _f.field_unlock()

    # Predict
    def predict(self, value, direction: access_e):
        for f in self.get_fields():
            f.field_predict((
                value >> f.get_lsb_pos()), path_t.FRONTDOOR, direction)

    # set prediction from parent to fields
    def set_prediction(self, pred_type: predict_t):
        for f in self.get_fields():
            f.set_prediction(pred_type)

    # Get mirrored value
    def get_mirrored_value(self):
        self._mirrored = 0
        for f in self.get_fields():
            updt_v = (f.get_value() << f.get_lsb_pos())
            self._mirrored = (self._mirrored | updt_v)
        return self._mirrored

    # get_address
    def get_address(self):
        return self._address

    # get desired value
    def get_desired(self):
        self._desired = 0
        for f in self._fields:
            self._desired = self._desired | (f.get() << f.get_lsb_pos())
        return self._desired

    # Reset
    def reset(self):
        for f in self._fields:
            f.reset()
            # placeholder to fix Flake8 line error
            value = (f.get_value() << f.get_lsb_pos())
            self._mirrored = self._mirrored | value

    # get_name
    def get_name(self) -> str:
        return self._name

    # Build internal function
    def build(self):
        '''
        This function needs to be implemented into the child class
        create each fields and invoke the configure from each field
        '''
        uvm_not_implemeneted(self.gen_message("Calling Build when not \
                                              implemented by the user"))

    # Write Method (TASK)
    async def write(self, value, map: uvm_reg_map,
                    path: path_t, check: check_t) -> uvm_resp_t:
        # This Task should implement the main read method via only FRONTDOOR
        # TODO: BACKDOOT and USER FRONTDOOR are missing
        # This Task returns only the operation status
        # Local Variables to be returned
        status = uvm_resp_t
        # TODO:
        # Given the map we do not check if the current register
        # exists in the map
        # (redundant check) since the register is directly taken from the MAP
        # We check instead if the map is set and if
        # only one exists (multiple access)
        # The map the register belongs to should not be unique
        # could easily be a list of MAPS
        # every map correspond a separate unique HW interface (BUS)
        # to the specific target register
        # the access should be carried out on each MAP
        # check if any operation is in progress for the given register
        if (self._op_in_progress is False):
            self._op_in_progress = True
            # TODO: Implement as FOR LOOP
            if map is not None:
                if value is not None:
                    status = await map.process_write_operation(
                        self.get_address(), value, path, check)
                elif (value is None):
                    status = await map.process_write_operation(
                        self.get_address(), self.get_desired(), path, check)
            else:
                error_out(self._header, "WRITE: map cannot be NULL")
            self._op_in_progress = False
        else:
            uvm_fatal(self._header, "write cannot perform an operation while \
                      another is in progress")
        # Return from Task
        return status

    # Read Method (TASK)
    async def read(self, map: uvm_reg_map, path: path_t, check: check_t):
        # This Task should implement the main read method via only FRONTDOOR
        # TODO: BACKDOOT and USER FRONTDOOR are missing
        # This Task returns only the operation status and the read value
        # (0 is status is error)
        # Local Variables to be returned
        status = uvm_resp_t
        # TODO:
        # Given the map we do not check if the current
        # register exists in the map
        # (redundant check) since the register is directly taken from the MAP
        # We check instead if the map
        # is set and if only one exists (multiple access)
        # The map the register belongs to should not be unique could easily\
        # be a list of MAPS
        # every map correspond a separate unique HW interface (BUS)
        # to the specific target register
        # the access should be carried out on each MAP
        # check if any operation is in progress for the given register
        if (self._op_in_progress is False):
            self._op_in_progress = True
            if map is not None:
                status, read_data = await map.process_read_operation(
                    self.get_address(), path, check)
                if status == uvm_resp_t.ERROR_RESP:
                    read_data = 0
            else:
                error_out(self._header, "READ: map cannot be NULL")
            self._op_in_progress = False
        else:
            uvm_fatal(self._header, "read cannot perform an operation while \
                      another is in progress")
        # Return from Task
        return status, read_data

    # Coverage API
    # set_coverage
    def set_coverage(self, is_on: bool):
        self._cover_on = self._has_cover and self._is_cover_on

    # sample_values
    def sample_values(self):
        uvm_not_implemeneted(self.gen_message("sample_values \
                                              used but not implemented"))
