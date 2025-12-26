import pytest

from pyuvm import uvm_hdl_path_concat, uvm_hdl_path_slice


def test_basic_slice():
    """
    Test uvm_hdl_path_slice object parameters
    """
    obj = uvm_hdl_path_slice("test_slice", -1, -1)
    assert obj.path == "test_slice"
    assert obj.offset == -1
    assert obj.size == -1


@pytest.mark.xfail(reason="Not implemented", raises=NotImplementedError)
def test_basic_uvm_hdl_path_concat():
    """
    Test uvm_hdl_path_concat object functions specified in section 17.2.3
    """
    # single slice register
    reg_slice = uvm_hdl_path_slice("reg_slice", -1, -1)
    reg_slice_concat_0 = uvm_hdl_path_concat("reg_slice_concat")
    reg_slice_concat_0.add_slice(reg_slice)
    test_slice_obj = reg_slice_concat_0.get_slices()
    assert len(test_slice_obj) == 1
    assert test_slice_obj[0].path == "reg_slice"
    assert test_slice_obj[0].offset == -1
    assert test_slice_obj[0].size == -1


@pytest.mark.xfail(reason="Not Implemented", raises=NotImplementedError)
def test_overlap_uvm_hdl_path_concat_0():
    """
    Test uvm_hdl_path_concat overlap detection
    """
    # test overlap with one DWORD register slice and a 4 bit register slice
    reg_slice_0 = uvm_hdl_path_slice("reg_slice_0", 0, 32)
    reg_slice_1 = uvm_hdl_path_slice("reg_slice_1", 8, 4)
    reg_slice_concat_0 = uvm_hdl_path_concat("reg_slice_concat")
    reg_slice_concat_0.add_slice(reg_slice_0)
    with pytest.raises(Exception):
        reg_slice_concat_0.add_slice(reg_slice_1)


@pytest.mark.xfail(reason="Not Implemented", raises=NotImplementedError)
def test_overlap_uvm_hdl_path_concat_1():
    reg_slice_0 = uvm_hdl_path_slice("reg_slice_0", 0, 32)
    reg_slice_1 = uvm_hdl_path_slice("reg_slice_1", 8, 4)
    reg_slice_concat = uvm_hdl_path_concat("reg_slice_concat")
    reg_slice_concat.add_slice(reg_slice_0)
    with pytest.raises(Exception):
        reg_slice_concat.add_slice(reg_slice_1)


@pytest.mark.xfail(reason="Not Implemented", raises=NotImplementedError)
def test_overlap_uvm_hdl_path_concat_set_slices():
    # test with non-overlapping and contiguous slices
    reg_slice_0 = uvm_hdl_path_slice("reg_slice_0", 0, 8)
    reg_slice_1 = uvm_hdl_path_slice("reg_slice_1", 8, 1)
    reg_slice_2 = uvm_hdl_path_slice("reg_slice_2", 9, 4)
    reg_slice_3 = uvm_hdl_path_slice("reg_slice_3", 13, 19)
    reg_slice_concat = uvm_hdl_path_concat("reg_slice_concat")
    reg_slices = [reg_slice_3, reg_slice_2, reg_slice_1, reg_slice_0]
    reg_slice_concat.set_slices(reg_slices)


@pytest.mark.xfail(reason="Not Implemented", raises=NotImplementedError)
def test_uvm_hdl_path_concat_set_slices_contiguous_wrong_order():
    # test with non-overlapping and contiguous slices but with error in order
    reg_slice_0 = uvm_hdl_path_slice("reg_slice_0", 0, 8)
    reg_slice_1 = uvm_hdl_path_slice("reg_slice_1", 8, 1)
    reg_slice_2 = uvm_hdl_path_slice("reg_slice_2", 9, 4)
    reg_slice_3 = uvm_hdl_path_slice("reg_slice_3", 13, 19)
    reg_slice_concat = uvm_hdl_path_concat("reg_slice_concat")
    reg_slices = [reg_slice_3, reg_slice_1, reg_slice_2, reg_slice_0]
    with pytest.raises(Exception):
        reg_slice_concat.set_slices(reg_slices)


@pytest.mark.xfail(reason="Not Implemented", raises=NotImplementedError)
def test_uvm_hdl_path_concat_set_slices_non_contiguous_offsets():
    # test with non-overlapping and contiguous slices but with error in order
    reg_slice_0 = uvm_hdl_path_slice("reg_slice_0", 0, 8)
    reg_slice_1 = uvm_hdl_path_slice("reg_slice_1", 9, 1)
    reg_slice_2 = uvm_hdl_path_slice("reg_slice_2", 15, 4)
    reg_slice_concat = uvm_hdl_path_concat("reg_slice_concat")
    reg_slices = [reg_slice_2, reg_slice_1, reg_slice_0]
    reg_slice_concat.set_slices(reg_slices)
