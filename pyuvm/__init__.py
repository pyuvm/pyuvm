# Support Modules
from pyuvm._error_classes import (
    UsePythonMethod,
    UVMBadPhase,
    UVMConfigError,
    UVMConfigItemNotFound,
    UVMError,
    UVMFactoryError,
    UVMFatalError,
    UVMNotImplemented,
    UVMSequenceError,
    UVMTLMConnectionError,
)

# Extension Modules
from pyuvm._extension_classes import test

# Section 18 Register Layer
from pyuvm._reg.uvm_mem import uvm_mem
from pyuvm._reg.uvm_mem_mam import (
    uvm_mem_mam,
    uvm_mem_mam_cfg,
    uvm_mem_mam_policy,
    uvm_mem_region,
)
from pyuvm._reg.uvm_reg import uvm_reg
from pyuvm._reg.uvm_reg_adapter import (
    uvm_reg_adapter,
    uvm_reg_tlm_adapter,
)
from pyuvm._reg.uvm_reg_backdoor import uvm_reg_backdoor
from pyuvm._reg.uvm_reg_block import uvm_reg_block
from pyuvm._reg.uvm_reg_cbs import (
    uvm_mem_cb,
    uvm_mem_cb_iter,
    uvm_reg_bd_cb,
    uvm_reg_bd_cb_iter,
    uvm_reg_cb,
    uvm_reg_cb_iter,
    uvm_reg_cbs,
    uvm_reg_field_cb,
    uvm_reg_field_cb_iter,
    uvm_reg_read_only_cbs,
    uvm_reg_write_only_cbs,
)
from pyuvm._reg.uvm_reg_field import uvm_reg_field
from pyuvm._reg.uvm_reg_fifo import uvm_reg_fifo
from pyuvm._reg.uvm_reg_file import uvm_reg_file
from pyuvm._reg.uvm_reg_indirect import (
    uvm_reg_indirect_data,
    uvm_reg_indirect_ftdr_seq,
)
from pyuvm._reg.uvm_reg_item import (
    uvm_reg_bus_op,
    uvm_reg_item,
)
from pyuvm._reg.uvm_reg_map import (
    uvm_reg_map,
    uvm_reg_map_info,
    uvm_reg_seq_base,
    uvm_reg_transaction_order_policy,
)
from pyuvm._reg.uvm_reg_model import (
    uvm_access_e,
    uvm_check_e,
    uvm_coverage_model_e,
    uvm_door_e,
    uvm_elem_kind_e,
    uvm_endianness_e,
    uvm_hdl_path_concat,
    uvm_hdl_path_slice,
    uvm_hier_e,
    uvm_object_string_pool,
    uvm_path_e,
    uvm_predict_e,
    uvm_reg_addr_logic_t,
    uvm_reg_addr_t,
    uvm_reg_byte_en_t,
    uvm_reg_cvr_t,
    uvm_reg_data_logic_t,
    uvm_reg_data_t,
    uvm_reg_frontdoor,
    uvm_reg_map_addr_range,
    uvm_reg_mem_test_e,
    uvm_status_e,
)
from pyuvm._reg.uvm_reg_predictor import uvm_reg_predictor
from pyuvm._reg.uvm_reg_sequence import uvm_reg_sequence
from pyuvm._reg.uvm_vreg import (
    uvm_vreg,
    uvm_vreg_cb,
    uvm_vreg_cb_iter,
    uvm_vreg_cbs,
)
from pyuvm._reg.uvm_vreg_field import (
    uvm_vreg_field,
    uvm_vreg_field_cb,
    uvm_vreg_field_cb_iter,
    uvm_vreg_field_cbs,
)

# Section 5
from pyuvm._s05_base_classes import (
    uvm_field_op,
    uvm_object,
    uvm_policy,
    uvm_transaction,
)

# Section 6
from pyuvm._s06_reporting_classes import uvm_report_object

# Section 8
from pyuvm._s08_factory_classes import uvm_factory

# Section 9
from pyuvm._s09_phasing import (
    uvm_bottomup_phase,
    uvm_build_phase,
    uvm_check_phase,
    uvm_common_phases,
    uvm_connect_phase,
    uvm_end_of_elaboration_phase,
    uvm_extract_phase,
    uvm_final_phase,
    uvm_phase,
    uvm_report_phase,
    uvm_run_phase,
    uvm_start_of_simulation_phase,
    uvm_threaded_execute_phase,
    uvm_topdown_phase,
)

# Section 10
from pyuvm._s10_synchronization_classes import (
    uvm_callback,
    uvm_callback_iter,
    uvm_callbacks,
    uvm_do_callbacks,
)

# Section 12
from pyuvm._s12_uvm_tlm_interfaces import (
    uvm_analysis_export,
    uvm_analysis_imp,
    uvm_analysis_port,
    uvm_blocking_get_export,
    uvm_blocking_get_peek_export,
    uvm_blocking_get_peek_port,
    uvm_blocking_get_port,
    uvm_blocking_master_export,
    uvm_blocking_master_port,
    uvm_blocking_peek_export,
    uvm_blocking_peek_port,
    uvm_blocking_put_export,
    uvm_blocking_put_port,
    uvm_blocking_slave_export,
    uvm_blocking_slave_port,
    uvm_blocking_transport_export,
    uvm_blocking_transport_port,
    uvm_export_base,
    uvm_get_export,
    uvm_get_peek_export,
    uvm_get_peek_port,
    uvm_get_port,
    uvm_master_export,
    uvm_master_port,
    uvm_nonblocking_get_export,
    uvm_nonblocking_get_peek_export,
    uvm_nonblocking_get_peek_port,
    uvm_nonblocking_get_port,
    uvm_nonblocking_master_export,
    uvm_nonblocking_master_port,
    uvm_nonblocking_peek_export,
    uvm_nonblocking_peek_port,
    uvm_nonblocking_put_export,
    uvm_nonblocking_put_port,
    uvm_nonblocking_slave_export,
    uvm_nonblocking_slave_port,
    uvm_nonblocking_transport_export,
    uvm_nonblocking_transport_port,
    uvm_peek_export,
    uvm_peek_port,
    uvm_port_base,
    uvm_put_export,
    uvm_put_port,
    uvm_slave_export,
    uvm_slave_port,
    uvm_tlm_analysis_fifo,
    uvm_tlm_fifo,
    uvm_tlm_fifo_base,
    uvm_tlm_req_rsp_channel,
    uvm_tlm_transport_channel,
    uvm_transport_export,
    uvm_transport_port,
)

# Section 13
from pyuvm._s13_predefined_component_classes import (
    uvm_active_passive_enum,
    uvm_agent,
    uvm_driver,
    uvm_env,
    uvm_monitor,
    uvm_scoreboard,
    uvm_subscriber,
    uvm_test,
)
from pyuvm._s13_uvm_component import (
    ConfigDB,
    uvm_component,
    uvm_root,
)

# Section 14, 15 (Done as fresh Python design)
from pyuvm._s14_15_python_sequences import (
    ResponseQueue,
    uvm_seq_item_export,
    uvm_seq_item_port,
    uvm_sequence,
    uvm_sequence_base,
    uvm_sequence_item,
    uvm_sequencer,
    uvm_sequencer_base,
)
from pyuvm._utility_classes import (
    FIFO_DEBUG,
    PYUVM_DEBUG,
    FactoryData,
    FactoryMeta,
    Objection,
    ObjectionHandler,
    Override,
    Singleton,
    UVM_ROOT_Singleton,
    UVMQueue,
    count_bits,
    uvm_void,
)
from pyuvm._version import __version__

__all__ = [
    # Error classes
    "UVMError",
    "UVMNotImplemented",
    "UsePythonMethod",
    "UVMFactoryError",
    "UVMTLMConnectionError",
    "UVMBadPhase",
    "UVMSequenceError",
    "UVMConfigError",
    "UVMConfigItemNotFound",
    "UVMFatalError",
    # Extension classes
    "test",
    # Register layer classes - uvm_mem
    "uvm_mem",
    # Register layer classes - uvm_mem_mam
    "uvm_mem_mam_cfg",
    "uvm_mem_mam",
    "uvm_mem_region",
    "uvm_mem_mam_policy",
    # Register layer classes - uvm_reg
    "uvm_reg",
    # Register layer classes - uvm_reg_adapter
    "uvm_reg_adapter",
    "uvm_reg_tlm_adapter",
    # Register layer classes - uvm_reg_backdoor
    "uvm_reg_backdoor",
    # Register layer classes - uvm_reg_block
    "uvm_reg_block",
    # Register layer classes - uvm_reg_cbs
    "uvm_reg_cbs",
    "uvm_reg_cb",
    "uvm_reg_cb_iter",
    "uvm_reg_bd_cb",
    "uvm_reg_bd_cb_iter",
    "uvm_mem_cb",
    "uvm_mem_cb_iter",
    "uvm_reg_field_cb",
    "uvm_reg_field_cb_iter",
    "uvm_reg_read_only_cbs",
    "uvm_reg_write_only_cbs",
    # Register layer classes - uvm_reg_field
    "uvm_reg_field",
    # Register layer classes - uvm_reg_fifo
    "uvm_reg_fifo",
    # Register layer classes - uvm_reg_file
    "uvm_reg_file",
    # Register layer classes - uvm_reg_indirect
    "uvm_reg_indirect_data",
    "uvm_reg_indirect_ftdr_seq",
    # Register layer classes - uvm_reg_item
    "uvm_reg_item",
    "uvm_reg_bus_op",
    # Register layer classes - uvm_reg_map
    "uvm_reg_map_info",
    "uvm_reg_transaction_order_policy",
    "uvm_reg_seq_base",
    "uvm_reg_map",
    # Register layer classes - uvm_reg_model
    "uvm_reg_data_t",
    "uvm_reg_data_logic_t",
    "uvm_reg_addr_t",
    "uvm_reg_addr_logic_t",
    "uvm_reg_byte_en_t",
    "uvm_reg_cvr_t",
    "uvm_hdl_path_slice",
    "uvm_status_e",
    "uvm_door_e",
    "uvm_path_e",
    "uvm_check_e",
    "uvm_endianness_e",
    "uvm_elem_kind_e",
    "uvm_access_e",
    "uvm_hier_e",
    "uvm_predict_e",
    "uvm_coverage_model_e",
    "uvm_reg_mem_test_e",
    "uvm_hdl_path_concat",
    "uvm_reg_frontdoor",
    "uvm_reg_map_addr_range",
    "uvm_object_string_pool",
    # Register layer classes - uvm_reg_predictor
    "uvm_reg_predictor",
    # Register layer classes - uvm_reg_sequence
    "uvm_reg_sequence",
    # Register layer classes - uvm_vreg
    "uvm_vreg",
    "uvm_vreg_cbs",
    "uvm_vreg_cb",
    "uvm_vreg_cb_iter",
    # Register layer classes - uvm_vreg_field
    "uvm_vreg_field",
    "uvm_vreg_field_cbs",
    "uvm_vreg_field_cb",
    "uvm_vreg_field_cb_iter",
    # Section 5 - Base classes
    "uvm_object",
    "uvm_field_op",
    "uvm_policy",
    "uvm_transaction",
    # Section 6 - Reporting classes
    "uvm_report_object",
    # Section 8 - Factory classes
    "uvm_factory",
    # Section 9 - Phasing classes
    "uvm_phase",
    "uvm_topdown_phase",
    "uvm_bottomup_phase",
    "uvm_threaded_execute_phase",
    "uvm_build_phase",
    "uvm_connect_phase",
    "uvm_end_of_elaboration_phase",
    "uvm_start_of_simulation_phase",
    "uvm_run_phase",
    "uvm_extract_phase",
    "uvm_check_phase",
    "uvm_report_phase",
    "uvm_final_phase",
    "uvm_common_phases",
    # Section 10 - Synchronization classes
    "uvm_callback",
    "uvm_callbacks",
    "uvm_callback_iter",
    # Section 12 - TLM interfaces
    "uvm_export_base",
    "uvm_port_base",
    "uvm_blocking_put_port",
    "uvm_nonblocking_put_port",
    "uvm_put_port",
    "uvm_blocking_get_port",
    "uvm_nonblocking_get_port",
    "uvm_get_port",
    "uvm_blocking_peek_port",
    "uvm_nonblocking_peek_port",
    "uvm_peek_port",
    "uvm_blocking_get_peek_port",
    "uvm_nonblocking_get_peek_port",
    "uvm_get_peek_port",
    "uvm_blocking_transport_port",
    "uvm_nonblocking_transport_port",
    "uvm_transport_port",
    "uvm_blocking_master_port",
    "uvm_nonblocking_master_port",
    "uvm_master_port",
    "uvm_blocking_slave_port",
    "uvm_nonblocking_slave_port",
    "uvm_slave_port",
    "uvm_analysis_imp",
    "uvm_analysis_port",
    "uvm_nonblocking_put_export",
    "uvm_blocking_put_export",
    "uvm_put_export",
    "uvm_nonblocking_get_export",
    "uvm_blocking_get_export",
    "uvm_get_export",
    "uvm_nonblocking_peek_export",
    "uvm_blocking_peek_export",
    "uvm_peek_export",
    "uvm_blocking_get_peek_export",
    "uvm_nonblocking_get_peek_export",
    "uvm_get_peek_export",
    "uvm_blocking_transport_export",
    "uvm_nonblocking_transport_export",
    "uvm_transport_export",
    "uvm_blocking_master_export",
    "uvm_nonblocking_master_export",
    "uvm_master_export",
    "uvm_blocking_slave_export",
    "uvm_nonblocking_slave_export",
    "uvm_slave_export",
    "uvm_analysis_export",
    "uvm_tlm_fifo_base",
    "uvm_tlm_fifo",
    "uvm_tlm_analysis_fifo",
    "uvm_tlm_req_rsp_channel",
    "uvm_tlm_transport_channel",
    # Section 13 - Predefined component classes
    "uvm_active_passive_enum",
    "uvm_test",
    "uvm_env",
    "uvm_agent",
    "uvm_monitor",
    "uvm_scoreboard",
    "uvm_driver",
    "uvm_subscriber",
    "uvm_component",
    "uvm_root",
    "ConfigDB",
    # Section 14, 15 - Sequences
    "ResponseQueue",
    "uvm_sequence_item",
    "uvm_seq_item_export",
    "uvm_seq_item_port",
    "uvm_sequencer",
    "uvm_sequencer_base",
    "uvm_sequence_base",
    "uvm_sequence",
    # Utility classes
    "FIFO_DEBUG",
    "PYUVM_DEBUG",
    "count_bits",
    "Singleton",
    "Override",
    "FactoryData",
    "FactoryMeta",
    "uvm_void",
    "UVM_ROOT_Singleton",
    "Objection",
    "ObjectionHandler",
    "UVMQueue",
    # Version
    "__version__",
]

# Set the __module__ attribute for all re-exported names.
# This is necessary for the documentation generation tools to link objects correctly.
for _name in __all__:
    # Skip non-classes and non-functions.
    if _name in {"__version__", "FIFO_DEBUG", "PYUVM_DEBUG", "uvm_common_phases"}:
        continue
    globals()[_name].__module__ = __name__
