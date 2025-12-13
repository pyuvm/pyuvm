import pytest

from pyuvm import uvm_component, uvm_root


@pytest.fixture()
def initialize_pyuvm(request):
    uvm_component.component_dict.clear()
    uvm_root.component_dict.clear()
    uvm_root.clear_singletons()
    pass
