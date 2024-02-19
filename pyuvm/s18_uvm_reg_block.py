from pyuvm import uvm_object
from pyuvm.s20_uvm_reg import uvm_reg
from pyuvm.s21_uvm_reg_map import uvm_reg_map
from pyuvm.s24_uvm_reg_includes import uvm_fatal, uvm_not_implemeneted

'''
    TODO: the following must be completed
    1.  implement add_vreg
    2.  implement remove_reg
    3.  implement add_mem
    4.  implement remove_mem
    5.  implement unregister_blk
    6.  implement write_reg or write_mem by name
    7.  implement read_reg or read_mem by name
    8.  implement get_virtual_fields in a unique field list
    9.  implement get_mem to return a list of memories
    10. implement get_default_hdl_path
    11. implement set_default_hdl_path
    12. implement set_hdl_path_root
    13. implement is_hdl_path_root
    14. implement get_full_hdl_path
    15. implement has_hdl_path
    16. implement add_hdl_path
    17. implement clear_hdl_path
    18. implement get_backdoor
    19. implement set_backdoor
    20. implement get_default_door
    21. implement set_default_door
    22. implement needs_update
    23. implement update
    24. implement mirror
    25. implement all the coverage APIs using COCOTB coverage report

    NOTE:   write/read_reg_by_name will not be implemented there is no need
            to run this command from the BLK
'''


class uvm_reg_block(uvm_object):
    def __init__(self, name="uvm_reg_block"):
        super().__init__(name)
        self._regs = []
        self.def_map = None
        self._is_locked = False
        self.hdl_paths = {}
        self.fields = []
        self.root_path = ""
        self.child_blk = []
        self.maps = []
        self.parent_blk = None
        # optimize this by using dicationries with
        # TUPLES (existence_bool, handle)
        self.blk_maping = {}
        self.map_mapping = {}
        self.reg_mapping = {}
        self.blk_name = name
        self.header = name + " -- "
        self._has_cover = False
        self._is_cover_ion = False
        self._cover_on = False

    # is_locked
    def is_locked(self) -> bool:
        return self._is_locked

    # gen_message
    def gen_message(self, txt="") -> str:
        return f"{self.header,txt}"

    # clear_hdl_path
    def clear_hdl_path(self, kind="RTL"):
        uvm_not_implemeneted(self.header)

    # add_hdl_path
    def add_hdl_path(self, path: str, kind="RTL"):
        uvm_not_implemeneted(self.header)

    # has_hdl_path
    def has_hdl_path(self, kind: str) -> bool:
        uvm_not_implemeneted(self.header)

    # get_hdl_path
    def get_hdl_path(self, paths: list, kind=""):
        uvm_not_implemeneted(self.header)

    # get_full_hdl_path
    def get_full_hdl_path(self, paths: list, kind="", separator="."):
        uvm_not_implemeneted(self.header)

    # set_lock
    def set_lock(self):
        self._is_locked = True

    # blk_set_reg_mapping
    def blk_set_reg_mapping(self, reg: uvm_reg):
        self.reg_mapping[reg.get_name()] = True

    # blk_is_reg_mapped
    def blk_is_reg_mapped(self, reg: uvm_reg) -> bool:
        return self.reg_mapping[reg.get_name()]

    # blk_is_child_mapped
    def blk_is_child_mapped(self, in_blk) -> bool:
        if (isinstance(in_blk, uvm_reg_block) is False):
            uvm_fatal(self.gen_message("blk_is_child_mapped -- input block \
                                       should be uvm_reg_block"))
        else:
            return self.blk_maping[in_blk.get_name()]

    # blk_set_map_mapping
    def blk_set_map_mapping(self, map_i: uvm_reg_map):
        self.map_mapping[map_i.get_name()] = 1

    # blk_is_map_mapped
    def blk_is_map_mapped(self, map_i: uvm_reg_map):
        self.map_mapping[map_i.get_name()] = 1

    # configure
    def configure_blk(self, parent, hdl_path):
        if (self.parent_blk is None):
            self.parent_blk = parent
            self.parent_blk.configure_blk(self)
        else:
            self.parent_blk = None
        # add HDL PATH as well
        self.add_hdl_path(hdl_path)

    # add_block
    def add_block(self, in_blk):
        if (isinstance(in_blk, uvm_reg_block) is False):
            uvm_fatal(self.gen_message("add_block -- input block must be \
                                       uvm_reg_block type"))
        # add to the BLK main mapping
        if (in_blk not in self.child_blk):
            self.blk_maping[in_blk.get_name()] = 1
            self.child_blk.append(in_blk)

    # blk_add_register
    def _add_register(self, reg):
        self._regs.append(reg)
        self.blk_set_reg_mapping(reg)

    # blk_get_def_map
    def blk_get_def_map(self):
        return self.def_map

    # get_blk_full_name
    def get_blk_full_name(self) -> str:
        if (self.parent_blk is None):
            self.blk_name
        else:
            self.parent_blk + "." + self.blk_name

    # blk_get_registers
    def _get_registers(self) -> list:
        local_reg_collector = []
        if self.is_locked() is True:
            for r in self._regs:
                if self.blk_is_reg_mapped(r) is True:
                    local_reg_collector.append(r)
            if len(self.child_blk) != 0:
                for b in self.child_blk:
                    local_reg_collector.append(b.blk_get_registers())
        else:
            uvm_fatal(self.gen_message("_get_registers -- register block must \
                                       be locked"))
        return local_reg_collector

    # blk_get_fields
    def blk_get_fields(self) -> list:
        local_field_collector = []
        for r in self.blk_get_registers():
            local_field_collector.append(r.get_fields())
        return local_field_collector

    # get_all_child_blk
    def get_all_child_blk(self) -> list:
        local_blk_collector = []
        for b in self.child_blk:
            if (self.blk_is_child_mapped(b) is True):
                local_blk_collector.append(b)
                local_blk_collector.append(b.get_all_child_blk())
        return local_blk_collector

    # blk_add_map
    def blk_add_map(self, map_i: uvm_reg_map):
        if (self.is_locked() is True):
            uvm_fatal(self.gen_message("blk_add_map -- register block should \
                                       be locked"))

        if map_i in self.map_mapping.keys() and \
           self.map_mapping[map_i] is True:
            uvm_fatal(self.header)
        else:
            self.maps.append(map_i)

        if (self.def_map is None):
            self.def_map = map_i

    # blk_create_map byte_addressing and byte_en
    # along with endianess not yet supported
    def blk_create_map(self, name: str, base_addr: int):
        lmap = uvm_reg_map.create(name)
        lmap.configure(self, base_addr)
        self.blk_add_map(lmap)

    # reset_blk
    def reset_blk(self):
        uvm_not_implemeneted(self.gen_message("reset_blk -- not implemented"))

    # set_default_map
    def set_default_map(self, mapi: uvm_reg_map):
        if self.blk_is_map_mapped(mapi) is True:
            self.def_map = mapi
        else:
            uvm_fatal(self.gen_message("set_default_map required only \
                                       internal Mapped maps as degfault map"))

    # get_map_by_name
    def get_map_by_name(self, namei: str):
        if self.map_mapping[namei] == 1:
            return [m for m in self.maps if (m.get_name() == namei)]
            # TODO: search into child_blk
        else:
            return None

    # get_reg_by_name
    def get_reg_by_name(self, namei: str):
        if self.reg_mapping[namei] == 1:
            return [r for r in self._regs if (r.get_name() == namei)]
            # TODO: search into child_blk maps
        else:
            return None

    # set_coverage
    def set_coverage(self, is_on: bool):
        self._cover_on = self._has_cover and self._is_cover_on

        for rg in self.regs:
            rg.set_coverage(is_on)

        for mm in self.mems:
            mm.set_coverage(is_on)

        for blk in self.blks:
            blk.set_coverage(is_on)

    # sample_values
    def sample_values(self):
        for rg in self.regs:
            rg.sample_values()

        for blk in self.blks:
            blk.sample_values()

    # add_coverage
    def add_coverage(self):
        uvm_not_implemeneted(self.gen_message("add coverage not implemented"))

    # has_coverage
    def has_coverage(self):
        return self._has_cover

    # get_coverage
    def get_coverage(self):
        if self.has_coverage() is True:
            return self._cover_on
        else:
            return 0

    # similar to convert2string
    def __str__(self) -> str:
        return f"   {self.gen_message} \
                    self._regs          : {self._regs      } \
                    self.def_map        : {self.def_map    } \
                    self._is_locked     : {self._is_locked } \
                    self.hdl_paths      : {self.hdl_paths  } \
                    self.fields         : {self.fields     } \
                    self.root_path      : {self.root_path  } \
                    self.child_blk      : {self.child_blk  } \
                    self.maps           : {self.maps       } \
                    self.parent_blk     : {self.parent_blk } \
                    self.blk_maping     : {self.blk_maping } \
                    self.map_mapping    : {self.map_mapping} \
                    self.reg_mapping    : {self.reg_mapping} \
                    self.blk_name       : {self.blk_name   }"
