VERILOG_SIM ?= icarus
VHDL_SIM ?= ghdl

.PHONY: cocotb_tests
cocotb_tests:
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
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C examples/TinyALU sim checkclean
	make SIM=$(VERILOG_SIM) TOPLEVEL_LANG=verilog -C examples/TinyALU_reg sim checkclean
	make SIM=$(VHDL_SIM)    TOPLEVEL_LANG=vhdl    -C examples/TinyALU sim checkclean
