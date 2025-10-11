from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, ClassVar

from pyuvm.reg.uvm_reg_item import uvm_reg_item
from pyuvm.reg.uvm_reg_map import uvm_reg_map
from pyuvm.reg.uvm_reg_model import (
    uvm_check_e,
    uvm_coverage_model_e,
    uvm_door_e,
    uvm_predict_e,
    uvm_status_e,
)
from pyuvm.s05_base_classes import uvm_object
from pyuvm.s24_uvm_reg_includes import uvm_resp_t

if TYPE_CHECKING:
    from pyuvm.reg.uvm_reg import uvm_reg
    from pyuvm.reg.uvm_reg_map import uvm_reg_map_info
    from pyuvm.reg.uvm_reg_model import (
        uvm_reg_byte_en_t,
        uvm_reg_data_t,
    )
    from pyuvm.s14_15_python_sequences import uvm_reg_item, uvm_sequence_base

__all__ = ["uvm_reg_field"]
logger = logging.getLogger("RegModel")


_PREDEFINED_POLICIES: set[str] = set(
    [
        "RO",  # no effect, R: no effect.
        "RW",  # as is, R: no effect.
        "RC",  # no effect, R: clears all bits.
        "RS",  # no effect, R: sets all bits.
        "WRC",  # as is, R: clears all bits.
        "WRS",  # as is, R: sets all bits.
        "WC",  # clears all bits, R: no effect.
        "WS",  # sets all bits, R: no effect.
        "WSRC",  # sets all bits, R: clears all bits.
        "WCRS",  # clears all bits, R: sets all bits.
        "W1C",  # 1/0 clears/no effect on matching bit, R: no effect.
        "W1S",  # 1/0 sets/no effect on matching bit, R: no effect.
        "W1T",  # 1/0 toggles/no effect on matching bit, R: no effect.
        "W0C",  # 1/0 no effect on/clears matching bit, R: no effect.
        "W0S",  # 1/0 no effect on/sets matching bit, R: no effect.
        "W0T",  # 1/0 no effect on/toggles matching bit, R: no effect.
        "W1SRC",  # 1/0sets/no effect on matching bit, R: clears all bits.
        "W1CRS",  # 1/0clears/no effect on matching bit, R: sets all bits.
        "W0SRC",  # 1/0no effect on/sets matching bit, R: clears all bits.
        "W0CRS",  # 1/0no effect on/clears matching bit, R: sets all bits.
        "WO",  # as is, R: error.
        "WOC",  # clears all bits, R: error.
        "WOS",  # sets all bits, R: error.
        # first one after HARD reset is as is,
        # other W have no effects, R: no effect.
        "W1",
        # first one after HARD reset is as is,
        # other W have no effects, R: error.
        "WO1",
        "NOACCESS",  # no effect, R: no effect.
    ]
)


class uvm_reg_field(uvm_object):
    _max_size: ClassVar[int] = 0
    _policy_names: ClassVar[set[str]] = _PREDEFINED_POLICIES
    _reg_field_registry: ClassVar[dict[str, uvm_reg_field]] = dict()

    def __init__(self, name: str = "uvm_reg_field") -> None:
        super().__init__(name)
        self.value: uvm_reg_data_t = 0
        self._parent: uvm_reg = None
        self._size: int = 0
        self._lsb_pos: int = -1
        self._access: str = "RW"
        self._volatile: bool = False
        self._reset: dict[str, uvm_reg_data_t] = dict()
        self._mirrored: uvm_reg_data_t = 0
        self._desired: uvm_reg_data_t = 0
        self._cover_on = uvm_coverage_model_e.UVM_NO_COVERAGE
        self._written: bool = False
        self._check = uvm_check_e.UVM_NO_CHECK
        self._individually_accessible: bool = False
        self._fname: str = ""
        self._lineno: int = 0

        # TODO: Remove backward compatibility
        self._response = uvm_resp_t.PASS_RESP

    def configure(
        self,
        parent: uvm_reg,
        size: int,
        lsb_pos: int,
        access: str,
        volatile: bool,
        reset: uvm_reg_data_t,
        has_reset: bool = None,  # TODO: Remove default value
        is_rand: bool = None,  # TODO: Remove default value
        individually_accessible: bool = None,  # TODO: Remove
        **kwargs,
    ) -> None:  # TODO: Remove
        self._parent = parent
        self._size = size
        self._lsb_pos = lsb_pos
        self._access = access
        self._volatile = volatile

        # TODO: Remove backward compatibility check
        if has_reset is None:
            warnings.warn(
                "The 'has_reset' argument must be specified", DeprecationWarning, 2
            )
            if reset is not None:
                has_reset = True
            else:
                has_reset = False
        # TODO: Remove backward compatibility check
        if is_rand is None:
            warnings.warn(
                "The 'is_rand' argument must be specified", DeprecationWarning, 2
            )
            is_rand = False
        # TODO: Remove backward compatibility check
        if individually_accessible is None:
            warnings.warn(
                "The 'individually_accessible' argument must be specified",
                DeprecationWarning,
                2,
            )
            individually_accessible = False
        # TODO: Remove backward compatibility check
        #       Check if named argument 'is_volatile' is present and issue a
        #       deprecation warning
        #       raise SyntaxError if named argument is unknown
        for arg, val in kwargs.items():
            if arg == "is_volatile":
                warnings.warn(
                    "The 'is_volatile' argument is deprecated, use 'volatile' instead",
                    DeprecationWarning,
                    2,
                )
                self._volatile = val
            else:
                raise SyntaxError(f"Unknown argument {repr(arg)}")
        if has_reset:
            self.set_reset(reset)

        if self._access not in uvm_reg_field._policy_names:
            # TODO: The fallback access policy in the official implementation
            #       is "RW". Should it we implement "NOACCESS"?
            logger.error(
                f"Access policy {repr(self._access)} for field "
                f"{repr(self.get_full_name())} is not a defined field. "
                f"setting to 'NOACCESS'"
            )
            self._access = "NOACCESS"

        if self._access in [
            "RO",
            "RC",
            "RS",
            "WC",
            "WS",
            "W1C",
            "W1S",
            "W1T",
            "W0C",
            "W0S",
            "W0T",
            "W1SRC",
            "W1CRS",
            "W0SRC",
            "W0CRS",
            "WSRC",
            "WCRS",
            "WOC",
            "WOS",
        ]:
            is_rand = False

        if not is_rand:
            self.set_rand_mode(False)

        self._parent._add_field(self)

    def get_full_name(self) -> str:
        return f"{self._parent.get_full_name()}.{self.get_name()}"

    def get_parent(self) -> uvm_reg:
        return self._parent

    def get_register(self) -> uvm_reg:
        return self._parent

    def get_lsb_pos(self) -> int:
        return self._lsb_pos

    def get_n_bits(self) -> int:
        return self._size

    @staticmethod
    def get_max_size() -> int:
        return uvm_reg_field._max_size

    def set_access(self, mode: str) -> str:
        old_access = self._access
        self._access = mode.upper()
        if self._access not in uvm_reg_field._policy_names:
            logger.error(
                f"Access policy {repr(self._access)} is not a defined field access policy"
            )
            self._access = old_access
        return old_access

    def set_rand_mode(self, rand_mode: bool) -> None:
        try:
            self.value.rand_mode = rand_mode
        except AttributeError:
            if rand_mode is True:
                raise NotImplementedError(
                    f"Randomization is not supported for type {repr(type(self.value))}"
                )

    @staticmethod
    def define_access(name: str) -> bool:
        name = name.upper()
        if name in uvm_reg_field._policy_names:
            return False
        uvm_reg_field._policy_names.add(name)
        return True

    def get_access(self, map: uvm_reg_map = None) -> str | None:
        access = self._access
        # TODO: Implement backdoor
        try:
            if map == uvm_reg_map.backdoor():
                return access
        except NotImplementedError:
            pass

        if self._parent.get_rights(map) in ["RW"]:
            return access
        elif self._parent.get_rights(map) in ["RO"]:
            if access in [
                "RW",
                "RO",
                "WC",
                "WS",
                "W1C",
                "W1S",
                "W1T",
                "W0C",
                "W0S",
                "W0T",
                "W1",
            ]:
                return "RO"
            elif access in ["RC", "WRC", "W1SRC", "W0SRC", "WSRC"]:
                return "RC"
            elif access in ["RS", "WRS", "W1CRS", "W0CRS", "WCRS"]:
                return "RS"
            elif access in ["WO", "WOC", "WOS", "WO1"]:
                return "NOACCESS"
        elif self._parent.get_rights(map) in ["WO"]:
            if access in ["RW", "WRC", "WRS"]:
                return "WO"
            elif access in ["W1SRC"]:
                return "W1S"
            elif access in ["W0SRC"]:
                return "W0S"
            elif access in ["W1CRS"]:
                return "W1C"
            elif access in ["W0CRS"]:
                return "W0C"
            elif access in ["WCRS"]:
                return "WC"
            elif access in ["W1"]:
                return "W1"
            elif access in ["W01"]:
                return "W01"
            elif access in ["WSRC"]:
                return "WS"
            elif access in ["RO", "RC", "RS"]:
                return "NOACCESS"
        else:
            logger.warning(
                f"Register {repr(self._parent.get_full_name())} "
                f"containing field {repr(self.get_name())} is mapped in map "
                f"{repr(map.get_full_name())} with unknown access rights "
                f"{repr(self._parent.get_rights(map))}"
            )
        return "NOACCESS"

    def is_known_access(self, map: uvm_reg_map = None) -> bool:
        return self.get_access(map) in self._policy_names

    def set_volatility(self, volatile: bool) -> None:
        self._volatile = volatile

    def is_volatile(self) -> bool:
        return self._volatile

    @staticmethod
    def get_field_by_full_name(name: str) -> uvm_reg_field:
        # TODO: Error handling
        return uvm_reg_field._reg_field_registry[name]

    @DeprecationWarning
    def set_field(self, value: int) -> None:
        warnings.warn(
            "The 'set_field' method is deprecated, use 'set' instead",
            DeprecationWarning,
            2,
        )
        self.set(value, fname="", lineno=0)

    def set(self, value: uvm_reg_data_t, fname: str = "", lineno: int = 0) -> None:
        self._fname = fname
        self._lineno = lineno
        # Define an all 1 values
        _mask = (1 << self._size) - 1

        # TODO: check if value given is bigger than the size of field

        # Ideally the set value should be checked against the parent
        # register being accessed.
        # if the parent is under WRITE there should be no set called.
        # Not yet implemenmted.
        #
        access = self.get_access()
        # Return value based on the access
        if access in ("RO", "RC", "RS", "NOACCESS"):
            self._desired = self._desired  # Leave the desired value stable
        elif access in ("RW", "WRC", "WRS", "WO"):
            self._desired = value
        elif access in ("WC", "WCRS", "WOC"):
            self._desired = 0
        elif access in ("WS", "WSRC", "WOS"):
            self._desired = _mask
        elif access in ("W1C", "W1CRS"):
            self._desired = self._desired & (~value)
        elif access in ("W1S", "W1SRC"):
            self._desired = self._desired | value
        elif access == "W1T":
            self._desired = self._desired ^ value
        elif access in ("W0C", "W0CRS"):
            self._desired = self._desired & value
        elif access in ("W0S", "W0SRC"):
            self._desired = self._desired | (~value & _mask)
        elif access == "W0T":
            self._desired = self._desired ^ (~value & _mask)
        elif access in ("W1", "WO1"):
            if self._has_been_writ is False:
                self._desired = value
        else:
            self._desired = value

    def get(self, fname: str = "", lineno: int = 0) -> uvm_reg_data_t:
        self._fname = fname
        self._lineno = lineno
        return self._desired

    def get_mirrored_value(self, fname: str = "", lineno: int = 0) -> uvm_reg_data_t:
        if self.is_volatile():
            logger.warning(
                "Mirrored value returned for volatile field "
                f"{repr(self.get_full_name())}, register "
                f"'{self._parent.get_full_name()} may not reflect "
                "the actual current value."
            )
        self._fname = fname
        self._lineno = lineno
        return self._mirrored

    def reset(self, kind: str = "HARD") -> None:
        if kind not in self._reset:
            return
        self._mirrored = self._reset[kind]
        self._desired = self._mirrored
        self.value = self._mirrored
        if kind == "HARD":
            self._written = False

    def get_reset(self, kind: str = "HARD") -> uvm_reg_data_t:
        if kind not in self._reset:
            return self._desired
        return self._reset[kind]

    def has_reset(self, kind: str = "HARD", delete: bool = False) -> bool:
        if kind not in self._reset:
            return False
        if delete:
            del self._reset[kind]
        return True

    def set_reset(self, value: uvm_reg_data_t, kind: str = "HARD") -> None:
        self._reset[kind] = value & ((1 << self._size) - 1)

    def needs_update(self) -> bool:
        if self.get_access() in ("RO", "RC", "RS"):
            return False
        return (self._desired != self._mirrored) | self._volatile

    async def write(
        self,
        value: uvm_reg_data_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def read(
        self,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def poke(
        self,
        value: uvm_reg_data_t,
        kind: str = "",
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def peek(
        self,
        kind: str = "",
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def mirror(
        self,
        check: uvm_check_e = uvm_check_e.UVM_NO_CHECK,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    def set_compare(self, check: uvm_check_e) -> None:
        self._check = check

    def get_compare(self) -> uvm_check_e:
        return self._check

    def is_indv_accessible(self, path: uvm_door_e, local_map: uvm_reg_map) -> bool:
        raise NotImplementedError

    def predict(
        self,
        value: uvm_reg_data_t,
        be: uvm_reg_byte_en_t = -1,
        kind: uvm_predict_e = uvm_predict_e.UVM_PREDICT_DIRECT,
        path: uvm_door_e = uvm_door_e.UVM_FRONTDOOR,
        map: uvm_reg_map = None,
        fname: str = "",
        lineno: int = 0,
    ) -> bool:
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

    def _predict(
        self, cur_val: uvm_reg_data_t, wr_val: uvm_reg_data_t, map: uvm_reg_map
    ) -> uvm_reg_data_t:
        mask = (1 << self.get_n_bits()) - 1
        access = self.get_access(map)
        if access in ["RO", "RC", "RS", "NOACCESS"]:
            return cur_val
        elif access in ["RW", "WRC", "WRS", "WO"]:
            return wr_val
        elif access in ["WC", "WCRS", "WOC"]:
            return 0
        elif access in ["WS", "WSRC", "WOS"]:
            return mask
        elif access in ["W1C", "W1CRS"]:
            return cur_val & ~mask
        elif access in ["W1S", "W1SRC"]:
            return cur_val | wr_val
        elif access in ["WT"]:
            return cur_val ^ wr_val
        elif access in ["W0C", "W0CRS"]:
            return cur_val & wr_val
        elif access in ["W0S", "W0SRC"]:
            return cur_val | (~wr_val & mask)
        elif access in ["W0T"]:
            return cur_val ^ (~wr_val & mask)
        elif access in ["W1", "WO1"]:
            if self._written:
                return cur_val
            else:
                return wr_val
        else:
            return wr_val

    def _update(self) -> uvm_reg_data_t:
        raise NotImplementedError

    def _check_access(self, rw: uvm_reg_item, map_info: uvm_reg_map_info) -> bool:
        raise NotImplementedError

    async def do_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def do_predict(
        self,
        rw: uvm_reg_item,
        kind: uvm_predict_e = uvm_predict_e.UVM_PREDICT_DIRECT,
        be: uvm_reg_byte_en_t = -1,
    ) -> None:
        field_value = rw.get_value(0) & ((1 << self.get_n_bits()) - 1)
        if rw.get_status() != uvm_status_e.UVM_NOT_OK:
            rw.set_status(uvm_status_e.UVM_IS_OK)
        if not be & 0b1:
            return
        self.fname = rw.get_fname()
        self.lineno = rw.get_line()
        if kind == uvm_predict_e.UVM_PREDICT_WRITE:
            if (
                rw.get_door() == uvm_door_e.UVM_FRONTDOOR
                or rw.get_door() == uvm_door_e.UVM_PREDICT
            ):
                field_value = self._predict(self._mirrored, field_value, rw.get_map())
            self.written = True
            # TODDO: implement callbacks
            # callbacks = uvm_reg_field_cb_iter(self)
            # for callback in self._callbacks:
            #     callback.post_predict(self, self._mirrored, field_value,
            #                           uvm_predict_e.UVM_PREDICT_WRITE,
            #                           rw.get_door(), rw.get_map())
            field_value &= (1 << self.get_n_bits()) - 1
        elif kind == uvm_predict_e.UVM_PREDICT_READ:
            if (
                rw.get_door() == uvm_door_e.UVM_FRONTDOOR
                or rw.get_door() == uvm_door_e.UVM_PREDICT
            ):
                access = self.get_access(rw.get_map())
                if access in ["RC", "WRC", "WSRC", "W1SRC", "W0SRC"]:
                    field_value = 0
                elif access in ["RS", "WRS", "WCRS", "W1CRS", "W0CRS"]:
                    field_value = (1 << self.get_n_bits()) - 1
                elif access in ["WO", "WOC", "WOS", "WO1", "NOACCESS"]:
                    return
            # TODO: implement callbacks
            # callbacks = uvm_reg_field_cb_iter(self)
            # for callback in self._callbacks:
            #     callback.post_predict(self, self._mirrored, field_value,
            #                           uvm_predict_e.UVM_PREDICT_READ,
            #                           rw.get_door(), rw.get_map())
            field_value &= (1 << self.get_n_bits()) - 1
        elif kind == uvm_predict_e.UVM_PREDICT_DIRECT:
            if self.parent.is_busy():
                logger.warning(
                    "Trying to predict value of field "
                    f"{repr(self.get_name())} while register "
                    f"{repr(self.parent.get_name())} is being "
                    "accessed."
                )
                rw.set_status(uvm_status_e.UVM_NOT_OK)
        self._mirrored = field_value
        self._desired = field_value
        self.value = field_value

    def pre_randomize(self) -> None:
        raise NotImplementedError

    def post_randomize(self) -> None:
        raise NotImplementedError

    async def pre_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def pre_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def field_lock(self) -> None:
        warnings.warn("The 'field_lock' method is deprecated", DeprecationWarning, 2)
        pass

    def get_value(self) -> uvm_reg_data_t:
        warnings.warn(
            "The 'get_value' method is deprecated, use 'get_mirrored_value' instead",
            DeprecationWarning,
            2,
        )
        return self.get_mirrored_value()

    def set_response(self, f_response):
        # warnings.warn("The 'set_response' method is deprecated",
        #               DeprecationWarning, 2)
        self._response = f_response

    def get_response(self):
        # warnings.warn("The 'get_response' method is deprecated",
        #               DeprecationWarning, 2)
        return self._response

    def set_throw_error_on_read(self, teor=False):
        # warnings.warn("The 'set_throw_error_on_read' method is deprecated",
        #               DeprecationWarning, 2)
        self.set_debug(error_on_read=teor)

    def set_throw_error_on_write(self, teow=False):
        # warnings.warn("The 'set_throw_error_on_write' method is deprecated",
        #               DeprecationWarning, 2)
        self.set_debug(error_on_write=teow)

    def set_debug(self, error_on_read=None, error_on_write=None):
        if error_on_read is not None:
            self._error_on_read = error_on_read
        if error_on_write is not None:
            self._error_on_write = error_on_write

    # TODO: Should this be dunder methods?
    # extern virtual function void do_print (uvm_printer printer);
    # extern virtual function string convert2string;
    # extern virtual function uvm_object clone();
    # extern virtual function void do_copy   (uvm_object rhs);
    # extern virtual function bit  do_compare (uvm_object  rhs,
    #                                         uvm_comparer comparer);
    # extern virtual function void do_pack (uvm_packer packer);
    # extern virtual function void do_unpack (uvm_packer packer);
