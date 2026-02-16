from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, ClassVar

from cocotb.triggers import Lock

from pyuvm._error_classes import UVMFatalError
from pyuvm._reg.uvm_reg_field import uvm_reg_field
from pyuvm._reg.uvm_reg_file import uvm_reg_file
from pyuvm._reg.uvm_reg_item import uvm_reg_item
from pyuvm._reg.uvm_reg_model import (
    uvm_access_e,
    uvm_check_e,
    uvm_door_e,
    uvm_elem_kind_e,
    uvm_predict_e,
    uvm_status_e,
)
from pyuvm._s05_base_classes import uvm_object

if TYPE_CHECKING:
    from pyuvm._reg.uvm_reg_backdoor import uvm_reg_backdoor
    from pyuvm._reg.uvm_reg_block import uvm_reg_block
    from pyuvm._reg.uvm_reg_item import uvm_reg_item
    from pyuvm._reg.uvm_reg_map import uvm_reg_map, uvm_reg_map_info
    from pyuvm._reg.uvm_reg_model import (
        uvm_hdl_path_concat,
        uvm_hdl_path_slice,
        uvm_reg_addr_t,
        uvm_reg_byte_en_t,
        uvm_reg_cvr_t,
        uvm_reg_data_t,
    )
    from pyuvm._reg.uvm_reg_sequence import uvm_reg_frontdoor
    from pyuvm._s14_15_python_sequences import uvm_sequence_base

__all__ = ["uvm_reg"]
logger = logging.getLogger("RegModel")


class uvm_reg(uvm_object):
    _max_size: ClassVar[int] = 0
    _reg_registry: ClassVar[dict[str, uvm_reg]] = {}

    def __init__(
        self, name="", n_bits: int = 0, has_coverage: int = 0, **kwargs
    ) -> None:
        super().__init__(name)
        if n_bits < 1:
            logger.error(f"Register {repr(self.get_name())} cannot have 0 bits")
            n_bits = 1
        self._locked: bool = False
        self._parent: uvm_reg_block = None
        self._regfile_parent: uvm_reg_file = None
        self._n_bits: int = n_bits
        self._n_used_bits: int = 0
        self._maps: list = []
        self._fields: list[uvm_reg_field] = []
        self._has_cover = has_coverage
        self._cover_on = 0
        self._atomic = Lock()
        self._process = None  # TODO: process
        self._fname: str = ""
        self._lineno: int = 0
        self._read_in_progress: bool = False
        self._write_in_progress: bool = False
        self._is_busy: bool = False
        self._backdoor: uvm_reg_backdoor = None
        self._hdl_paths_pool: dict[str, list[str]] = dict()

        # TODO: remove backward compatibility
        self._addr = None
        for arg, val in kwargs.items():
            if arg == "reg_width":
                self._n_bits = val
                warnings.warn(
                    "The 'reg_width' argument is deprecated, use 'n_bits' instead",
                    DeprecationWarning,
                    2,
                )
            else:
                raise SyntaxError(f"Unknown argument {arg}")
        uvm_reg._max_size = max(uvm_reg._max_size, self._n_bits)

    def configure(
        self,
        blk_parent: uvm_reg_block,
        regfile_parent: uvm_reg_file = None,
        hdl_path: str = "",
        throw_error_on_read: bool = False,
        throw_error_on_write: bool = False,
        **kwargs,
    ) -> None:
        # TODO: remove backward compatibility
        if (
            not isinstance(regfile_parent, uvm_reg_file) and regfile_parent is not None
        ) or "addr" in kwargs:
            warnings.warn(
                "The 'configure' definition as changed, the address should be "
                "specified when the register is added to a map "
                "'blk_parent' instead",
                DeprecationWarning,
                2,
            )
            for arg, val in kwargs.items():
                if arg == "addr":
                    self._addr = val
                else:
                    raise SyntaxError(f"Unknown argument {arg}")
            if (
                not isinstance(regfile_parent, uvm_reg_file)
                or regfile_parent is not None
            ):
                self._addr = regfile_parent
        # END: backward compatibility

        if blk_parent is None:
            logger.error(
                "uvm_reg.configure() called without a parent block "
                f"for instance {self.get_name()} of register type "
                f"{self.get_type_name()}."
            )
            return
        self._parent = blk_parent
        self._parent._add_register(self)
        # TODO: remove backward compatibility
        if self._addr is not None:
            try:
                self.build()
            except AttributeError:
                logger.error(
                    "Calling build() when not implemented by user\n"
                    "This is not the way to go, this is only for "
                    "backward compatibility, please follow the UVM "
                    "guidelines"
                )
                raise
        else:
            # END: backward compatibility
            self._regfile_parent = regfile_parent
        if hdl_path != "":
            self.add_hdl_path_slice(hdl_path, -1, -1)
        # TODO: remove backward compatibility
        try:
            if throw_error_on_read is None or throw_error_on_read is not None:
                pass
        except NameError:
            warnings.warn("The 'throw_error_on_read' argument is deprecated")
        try:
            if throw_error_on_write is None or throw_error_on_write is not None:
                pass
        except NameError:
            warnings.warn("The 'throw_error_on_write' argument is deprecated")
        # END: backward compatibility

    def set_offset(
        self, map: uvm_reg_map, offset: uvm_reg_addr_t, unmapped: bool = False
    ) -> None:
        if len(self._maps) > 1 and not map:
            logger.error(
                f"'set_offset' requires a map when register "
                f"{repr(self.get_full_name())} belongs to more than one map."
            )
            return
        local_map = self.get_local_map(map)
        if local_map:
            local_map._set_reg_offset(self, offset, unmapped)

    def _set_parent(
        self, blk_parent: uvm_reg_block, regfile_parent: uvm_reg_file
    ) -> None:
        raise NotImplementedError

    def _add_field(self, field: uvm_reg_field) -> None:
        if self._locked:
            logger.error("Cannot add field to a locked register model")
            return
        if field is None:
            raise UVMFatalError("Field cannot be None")
        if field in self._fields:
            logger.error(f"Field {field.get_name()} is already added")

        # NOTE: add field and sort by lsb
        self._fields.append(field)
        self._fields.sort(key=lambda f: f.get_lsb_pos())

        # NOTE: Check if any fields are too large for the register
        for f in self._fields:
            if f.get_lsb_pos() + f.get_n_bits() > self.get_n_bits():
                logger.error(
                    f"Field {f.get_name()} is too large for register {self.get_name()}"
                )

        # NOTE: Check if any fields overlap
        for i in range(len(self._fields) - 1):
            msb = self._fields[i].get_lsb_pos() + self._fields[i].get_n_bits()
            if msb > self._fields[i + 1].get_lsb_pos():
                logger.error(
                    f"Field {self._fields[i].get_name()} overlaps "
                    f"field {self._fields[i + 1].get_name()} in register "
                    f"{self.get_name()}"
                )

    def add_map(self, map: uvm_reg_map) -> None:
        if map in self._maps:
            logger.error(f"Map {repr(map.get_name())} is already added")
        else:
            self._maps.append(map)

    def _lock_model(self) -> None:
        if self._locked:
            return
        uvm_reg._reg_registry[self.get_full_name()] = self
        for field in self._fields:
            uvm_reg_field._reg_field_registry[field.get_full_name()] = field
        self._locked = True

    def _unlock_model(self) -> None:
        del uvm_reg._reg_registry[self.get_full_name()]
        for field in self._fields:
            del uvm_reg_field._reg_field_registry[field.get_full_name()]
        self._locked = False

    def unregister(self, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        if self._regfile_parent is not None:
            return f"{self._regfile_parent.get_full_name()}.{self.get_name()}"
        if self._parent is not None:
            return f"{self._parent.get_full_name()}.{self.get_name()}"
        return self.get_name()

    def get_parent(self) -> uvm_reg_block:
        return self.get_block()

    def get_block(self) -> uvm_reg_block:
        return self._parent

    def get_regfile(self) -> uvm_reg_file:
        return self._regfile_parent

    def get_n_maps(self) -> int:
        return len(self._maps)

    def is_in_map(self, map: uvm_reg_map) -> bool:
        if map in self._maps:
            return True
        for local_map in self._maps:
            parent_map = local_map.get_parent_map()
            while parent_map is not None:
                if parent_map == map:
                    return True
                parent_map = parent_map.get_parent_map()
        return False

    def get_maps(self, maps: list[uvm_reg_map]) -> None:
        # NOTE: The list is mutable, emulate the pass by reference
        maps.clear()
        for i in self._maps:
            maps.append(i)

    def get_local_map(self, map: uvm_reg_map) -> uvm_reg_map | None:
        if map is None:
            return self.get_default_map()
        if map in self._maps:
            return map
        for local_map in self._maps:
            parent_map = local_map.get_parent_map()
            while parent_map is not None:
                if parent_map == map:
                    return local_map
                parent_map = parent_map.get_parent_map()
        logger.warning(
            f"Register {self.get_full_name()} is not contained "
            f"within map {map.get_full_name()}"
        )
        return None

    def get_default_map(self) -> uvm_reg_map | None:
        if len(self._maps) == 0:
            logger.warning(
                f"Register {self.get_full_name()} is not registered with any map"
            )
            return None
        if len(self._maps) == 1:
            return self._maps[0]
        for map in self._maps:
            blk = map.get_parent()
            default_map = blk.get_default_map()
            if default_map is not None:
                local_map = self.get_local_map(default_map)
                if local_map is not None:
                    return local_map
        return self._maps[0]

    def get_rights(self, map: uvm_reg_map = None) -> str:
        local_map = self.get_local_map(map)
        if local_map is None:
            return "RW"
        info = local_map.get_reg_map_info(self)
        return info.rights

    def get_n_bits(self) -> int:
        return self._n_bits

    def get_n_bytes(self) -> int:
        return int((self.get_n_bits() - 1) / 8 + 1)

    @staticmethod
    def get_max_size() -> int:
        return uvm_reg._max_size

    # TODO: Document definition compared to IEEE 1800.2
    def get_fields(self) -> list[uvm_reg_field]:
        return self._fields

    def get_field_by_name(self, name: str) -> uvm_reg_field:
        raise NotImplementedError

    def _get_fields_access(self, map: uvm_reg_map) -> str:
        readable = False
        writable = False
        for field in self._fields:
            access = field.get_access(map)
            if access in ["RO", "RC", "RS"]:
                readable = True
            elif access in ["WO", "WOC", "WS", "WO1"]:
                writable = True
            else:
                return "RW"
            if readable and writable:
                return "RW"
        if writable and not readable:
            return "WO"
        elif readable and not writable:
            return "RO"
        return "RW"

    def get_offset(self, map: uvm_reg_map) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_address(self, map: uvm_reg_map = None) -> uvm_reg_addr_t:
        # TODO: remove backward compatibility
        if self._addr is not None:
            return self._addr
        # END: backward compatibility
        _, addr = self.get_addresses(map)
        return addr[0]

    def get_addresses(
        self,
        map: uvm_reg_map = None,
    ) -> tuple[int, list[uvm_reg_addr_t]]:
        local_map = self.get_local_map(map)
        if local_map is None:
            return -1
        map_info = local_map.get_reg_map_info(self)
        if map_info.unmapped:
            if map is None:
                map_name = local_map.get_full_name()
            else:
                map_name = map.get_full_name()
            logger.warning(
                f"Register {repr(self.get_name())} is unmapped in map {repr(map_name)}"
            )
        return local_map.get_n_bytes(), map_info.addr

    @staticmethod
    def get_reg_by_full_name(full_name: str) -> uvm_reg | None:
        return uvm_reg._reg_registry.get(full_name)

    def set(self, value: uvm_reg_data_t, fname: str = "", lineno: int = 0) -> None:
        self.fname = fname
        self._lineno = lineno
        for field in self._fields:
            field.set((value >> field.get_lsb_pos()) & ((1 << field.get_n_bits()) - 1))

    def get(self, fname: str = "", lineno: int = 0) -> uvm_reg_data_t:
        self.fname = fname
        self._lineno = lineno
        value = 0
        for field in self._fields:
            value |= field.get() << field.get_lsb_pos()
        return value

    def get_mirrored_value(self, fname: str = "", lineno: int = 0) -> int:
        self.fname = fname
        self._lineno = lineno
        value = 0
        for field in self._fields:
            value |= field.get_mirrored_value() << field.get_lsb_pos()
        return value

    def needs_update() -> bool:
        raise NotImplementedError

    def reset(self, kind: str = "HARD") -> None:
        for field in self._fields:
            field.reset(kind)
        try:
            if self._atomic.locked():
                self._atomic.release()
        except TypeError:
            # INFO: For backward compatibility with Cocotb <= 1.8
            if self._atomic.locked:
                self._atomic.release()

        self._process = None
        self._set_is_busy(False)

    def get_reset(self, kind: str = "HARD") -> int:
        raise NotImplementedError

    def has_reset(self, kind: str = "HARD", delete: bool = False) -> bool:
        raise NotImplementedError

    def set_reset(self, value: uvm_reg_data_t, kind: str = "HARD") -> None:
        raise NotImplementedError

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
        **kwargs,
    ) -> uvm_status_e:
        # TODO: remove backward compatibility
        if not isinstance(path, uvm_door_e):
            warnings.warn(
                "The 'write' arguments has changed in order to "
                "match the IEEE 1800.2 standard.",
                DeprecationWarning,
                2,
            )
            _map = path
            path = map
            map = _map
        if "check" in kwargs:
            warnings.warn("The 'check' arguments is deprecated", DeprecationWarning, 2)
        # END

        async with self._atomic:
            self.set(value)
            rw = uvm_reg_item("write_item")
            rw.set_element(self)
            rw.set_kind(uvm_access_e.UVM_WRITE)
            rw.set_value(value)
            rw.set_door(path)
            rw.set_map(map)
            rw.set_parent_sequence(parent)
            rw.set_priority(prior)
            rw.set_extension(extension)
            rw.set_fname(fname)
            rw.set_line(lineno)
            await self.do_write(rw)
        return rw.get_status()

    async def read(
        self,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
        **kwargs,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        # TODO: remove backward compatibility
        if not isinstance(path, uvm_door_e):
            warnings.warn(
                "The 'read' arguments has changed in order to "
                "match IEEE 1800.2 standard.",
                DeprecationWarning,
                2,
            )
            _map = path
            path = map
            map = _map
        if "check" in kwargs:
            warnings.warn("The 'check' argument is deprecated", DeprecationWarning, 2)
        # END
        async with self._atomic:
            status, value = await self._read(
                path, map, parent, prior, extension, fname, lineno
            )
        return status, value

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

    async def update(
        self,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
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

    def is_busy(self) -> bool:
        return self._is_busy

    def _set_is_busy(self, busy: bool) -> None:
        self._is_busy = busy

    async def _read(
        self,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        rw = uvm_reg_item("read_item")
        rw.set_element(self)
        rw.set_element_kind(uvm_elem_kind_e.UVM_REG)
        rw.set_value(0)
        rw.set_door(path)
        rw.set_map(map)
        rw.set_parent_sequence(parent)
        rw.set_priority(prior)
        rw.set_extension(extension)
        rw.set_fname(fname)
        rw.set_line(lineno)
        await self.do_read(rw)
        return rw.get_status(), rw.get_value()

    def _check_access(self, rw: uvm_reg_item) -> tuple[bool, uvm_reg_map_info | None]:
        map_info = None
        if rw.get_door() == uvm_door_e.UVM_DEFAULT_DOOR:
            rw.set_door(self._parent.get_default_door())
        if rw.get_door() == uvm_door_e.UVM_BACKDOOR:
            raise NotImplementedError
        if rw.get_door() != uvm_door_e.UVM_BACKDOOR:
            tmp_map = rw.get_map()
            rw.set_local_map(self.get_local_map(tmp_map))
            if not rw.get_local_map():
                # TODO: Error message
                rw.set_status(uvm_status_e.UVM_NOT_OK)
                return False, None
            tmp_local_map = rw.get_local_map()
            map_info = tmp_local_map.get_reg_map_info(self)
            if not map_info.frontdoor and map_info.unmapped:
                # TODO: Error message
                rw.set_status(uvm_status_e.UVM_NOT_OK)
                return False, None
            if not tmp_map:
                rw.set_map(tmp_local_map)
        return True, map_info

    def do_check(
        self, expected: uvm_reg_data_t, actual: uvm_reg_data_t, map: uvm_reg_map
    ) -> bool:
        raise NotImplementedError

    async def do_write(self, rw: uvm_reg_item) -> None:
        self.fname = rw.get_fname()
        self.lineno = rw.get_line()
        rc, map_info = self._check_access(rw)
        if not rc:
            return
        self._write_in_progress = True
        value = rw.get_value() & (1 << self.get_n_bits()) - 1
        rw.set_value(value)
        rw.set_status(uvm_status_e.UVM_IS_OK)
        # TODO: pre_write fields callbacks
        # TODO: pre_write reg callbacks
        door = rw.get_door()
        if door == uvm_door_e.UVM_BACKDOOR:
            await self._do_write_backdoor(rw, map_info)
        elif door == uvm_door_e.UVM_FRONTDOOR:
            await self._do_write_frontdoor(rw, map_info)
        # TODO: post_write reg callbacks
        # TODO: post_write fields callbacks
        # TODO: report
        self._write_in_progress = False

    async def _do_write_backdoor(
        self, rw: uvm_reg_item, map_info: uvm_reg_map_info
    ) -> None:
        raise NotImplementedError

    async def _do_write_frontdoor(
        self, rw: uvm_reg_item, map_info: uvm_reg_map_info
    ) -> None:
        local_map = rw.get_local_map()
        system_map = local_map.get_root_map()
        self._set_is_busy(True)
        # INFO: User frontdoor
        if map_info.frontdoor is not None:
            frontdoor = map_info.frontdoor
            frontdoor.atomic_lock()
            frontdoor.rw_info = rw
            if frontdoor.sequencer is None:
                frontdoor.sequencer = system_map.get_sequencer()
            frontdoor.start(frontdoor.sequencer, rw.get_parent_sequence())
            frontdoor.atomic_unlock()
        # INFO: Built in frontdoor
        else:
            await local_map.do_write(rw)
        self._set_is_busy(False)
        if system_map.get_auto_predict():
            if rw.get_status() != uvm_status_e.UVM_NOT_OK:
                self.sample(rw.get_value(), -1, False, rw.get_map())
                self._parent._sample(map_info.offset, False, rw.get_map())
            status = rw.get_status()
            self.do_predict(rw, uvm_predict_e.UVM_PREDICT_WRITE)
            rw.set_status(status)

    async def do_read(self, rw: uvm_reg_item) -> None:
        self._fname = rw.get_fname()
        self._lineno = rw.get_line()
        rc, map_info = self._check_access(rw)
        if not rc:
            return
        self._read_in_progress = True
        rw.set_status(uvm_status_e.UVM_IS_OK)
        # TODO: pre_read fields callbacks
        # TODO: pre_read reg callbacks
        door = rw.get_door()
        if door == uvm_door_e.UVM_BACKDOOR:
            await self._do_read_backdoor(rw, map_info)
        elif door == uvm_door_e.UVM_FRONTDOOR:
            await self._do_read_frontdoor(rw, map_info)
        # TODO: post_read reg callbacks
        # TODO: post_read fields callbacks
        # TODO: report
        self._read_in_progress = False

    async def _do_read_backdoor(
        self, rw: uvm_reg_item, map_info: uvm_reg_map_info
    ) -> None:
        raise NotImplementedError

    async def _do_read_frontdoor(
        self, rw: uvm_reg_item, map_info: uvm_reg_map_info
    ) -> None:
        local_map = rw.get_local_map()
        system_map = local_map.get_root_map()
        self._set_is_busy(True)
        if local_map.get_check_on_read():
            exp_value = self.get_mirrored_value()
        if map_info.frontdoor:
            frontdoor = map_info.frontdoor
            frontdoor.atomic_lock()
            frontdoor.rw_info = rw
            if not frontdoor.sequencer:
                frontdoor.sequencer = system_map.get_sequencer()
            frontdoor.start(frontdoor.sequencer, rw.get_parent_sequence())
            frontdoor.atomic_unlock()
        else:  # Built-in frontdoor
            await local_map.do_read(rw)
        self._set_is_busy(False)
        if system_map.get_auto_predict():
            if (
                local_map.get_check_on_read()
                and rw.get_status() != uvm_status_e.UVM_NOT_OK
            ):
                self.do_check(exp_value, rw.get_value(), system_map)
            if rw.get_status() != uvm_status_e.UVM_NOT_OK:
                # TODO: sample
                pass
            status = rw.get_status()
            self.do_predict(rw, uvm_predict_e.UVM_PREDICT_READ)
            rw.set_status(status)

    def do_predict(
        self, rw: uvm_reg_item, kind: uvm_predict_e, be: uvm_reg_byte_en_t = -1
    ) -> None:
        reg_value = rw.get_value()
        self._fname = rw.get_fname()
        self._lineno = rw.get_line()
        if rw.get_status() == uvm_status_e.UVM_IS_OK:
            if self.is_busy() and kind == uvm_predict_e.UVM_PREDICT_DIRECT:
                logger.warning(
                    "Trying to predict value of register "
                    f"{repr(self.get_name())} while it is being accessed"
                )
                return
            for field in self.get_fields():
                rw.set_value(
                    (reg_value >> field.get_lsb_pos()) & ((1 << field.get_n_bits()) - 1)
                )
                byte_enable = be >> (int(field.get_lsb_pos() / 8))
                field.do_predict(rw, kind, byte_enable)
            rw.set_value(reg_value)
        else:
            logger.warning("Status UVM_NOT_OK; skipping prediction.")

    def set_frontdoor(
        self,
        ftdr: uvm_reg_frontdoor,
        map: uvm_reg_map = None,
        fname: str = "",
        lineno: int = 0,
    ) -> None:
        raise NotImplementedError

    def get_frontdoor(self, map: uvm_reg_map = None) -> uvm_reg_frontdoor:
        raise NotImplementedError

    def set_backdoor(
        self, bkdr: uvm_reg_backdoor, fname: str = "", lineno: int = 0
    ) -> None:
        raise NotImplementedError

    def get_backdoor(self, inherited: bool = True) -> uvm_reg_backdoor:
        raise NotImplementedError

    def clear_hdl_path(self, kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path(self, slices: list[uvm_hdl_path_slice], kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path_slice(
        self, name: str, offset: int, size: int, first: bool = False, kind: str = "RTL"
    ) -> None:
        # TODO: implement offset and size
        paths = self._hdl_paths_pool.get(kind)
        if not paths or first:
            self._hdl_paths_pool[kind] = name
        else:
            self._hdl_paths_pool[kind].append(name)

    def has_hdl_path(self, kind: str = "") -> bool:
        raise NotImplementedError

    # TODO: Check method definition
    def get_hdl_path(self, paths: list[uvm_hdl_path_concat], kind: str = "") -> None:
        raise NotImplementedError

    # TODO: Check method definition
    def get_hdl_path_kind(self, kinds: list[str]) -> None:
        raise NotImplementedError

    def get_full_hdl_path(
        self, paths: list[uvm_hdl_path_concat], kind: str = "", separator: str = "."
    ) -> None:
        raise NotImplementedError

    async def backdoor_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def backdoor_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def backdoor_read_func(self, rw: uvm_reg_item) -> uvm_status_e:
        raise NotImplementedError

    def backdoor_watch(self) -> None:
        raise NotImplementedError

    def include_coverage(
        self, scope: str, models: uvm_reg_cvr_t, accessor: uvm_object = None
    ) -> None:
        raise NotImplementedError

    def build_coverage(self, models: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def add_coverage(self, models: uvm_reg_cvr_t) -> None:
        raise NotImplementedError

    def has_coverage(self, models: uvm_reg_cvr_t) -> bool:
        raise NotImplementedError

    def set_coverage(self, is_on: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def get_coverage(self, is_on: uvm_reg_cvr_t) -> bool:
        raise NotImplementedError

    def sample(
        self,
        data: uvm_reg_data_t,
        byte_en: uvm_reg_data_t,
        is_read: bool,
        map: uvm_reg_map,
    ) -> None:
        raise NotImplementedError

    def sample_values(self) -> None:
        raise NotImplementedError

    def _sample(
        self,
        data: uvm_reg_data_t,
        byte_en: uvm_reg_data_t,
        is_read: bool,
        map: uvm_reg_map,
    ) -> None:
        self.sample(data, byte_en, is_read, map)

    # TODO: register callback
    # `uvm_register_cb(uvm_reg, uvm_reg_cbs)

    async def pre_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def pre_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def get_reg_size(self) -> int:
        warnings.warn(
            "The 'get_reg_size' method is deprecated, use 'get_n_bits' instead",
            DeprecationWarning,
            2,
        )
        return self.get_n_bits()

    @property
    def n_bits(self) -> int:
        warnings.warn(
            "The 'n_bits' attribute is deprecated, use the method 'get_n_bits' instead",
            DeprecationWarning,
            2,
        )
        return self.get_n_bits()

    def check_err_list(self) -> None:
        warnings.warn(
            "The 'check_err_list' method is deprecated", DeprecationWarning, 2
        )

    def _set_lock(self) -> None:
        warnings.warn("The '_set_lock' method is deprecated", DeprecationWarning, 2)

    def set_desired(self, value):
        warnings.warn(
            "The 'set_desired' method is deprecated, use 'set' instead",
            DeprecationWarning,
            2,
        )
        self.set(value)

    def get_desired(self):
        warnings.warn(
            "The 'get_desired' method is deprecated, use 'get' instead",
            DeprecationWarning,
            2,
        )
        return self.get()

    def get_access_policy(self):
        warnings.warn(
            "The 'get_access_policy' method is deprecated, use 'get_rights' instead",
            DeprecationWarning,
            2,
        )
        return self.get_rights()


# TODO: Should this be dunder methods?
#   extern virtual function void            do_print (uvm_printer printer);
#   extern virtual function string          convert2string();
#   extern virtual function uvm_object      clone      ();
#   extern virtual function void            do_copy    (uvm_object rhs);
#   extern virtual function bit             do_compare (uvm_object  rhs,
#                                                       uvm_comparer comparer);
#   extern virtual function void            do_pack    (uvm_packer packer);
#   extern virtual function void            do_unpack  (uvm_packer packer);
