VERILOG_SIM ?= icarus
VHDL_SIM ?= ghdl

.PHONY: tests pytests cocotb_tests cocotb_verilog_tests cocotb_vhdl_tests

tests: pytests cocotb_tests

pytests:
	pytest tests/pytests

cocotb_tests: cocotb_verilog_tests cocotb_vhdl_tests

cocotb_verilog_tests:
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/queue sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/run_phase sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/decorator sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/t05_base_classes sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/t08_factories sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/t09_phasing sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/t12_tlm sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/t13_components sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/config_db sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/t14_15_sequences sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/ext_classes sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C tests/cocotb_tests/test_ral_read_write sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C examples/TinyALU sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C examples/TinyALU_reg sim checkclean

cocotb_vhdl_tests:
	make SIM=$(VHDL_SIM)    TOPLEVEL_LANG=vhdl    -C examples/TinyALU sim checkclean
