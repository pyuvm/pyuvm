CWD=$(shell pwd)
export COCOTB_REDUCED_LOG_FMT = 1
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
MAX_QUIT_COUNTS ?= 0 1 2 25
MAX_QUIT_TEST_FILTER ?= AluTestErrors
ifeq ($(TOPLEVEL_LANG),verilog)
	VERILOG_SOURCES =$(CWD)/../TinyALU/hdl/verilog/tinyalu.sv
else ifeq ($(TOPLEVEL_LANG),vhdl)
	VHDL_SOURCES=$(CWD)/../TinyALU/hdl/vhdl/single_cycle_add_and_xor.vhd \
				$(CWD)/../TinyALU/hdl/vhdl/three_cycle_mult.vhd \
				$(CWD)/../TinyALU/hdl/vhdl/tinyalu.vhd
else
    $(error "A valid value (verilog or vhdl) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG)")
endif
ifeq ($(SIM), verilator)
    # Enable processing of #delay statements
    COMPILE_ARGS += --timing
endif
MODULE := testbench
TOPLEVEL = tinyalu
GHDL_ARGS := --ieee=synopsys
COCOTB_HDL_TIMEUNIT = 1us
COCOTB_HDL_TIMEPRECISION = 1us
include $(shell cocotb-config --makefiles)/Makefile.sim
include ../../checkclean.mk

.PHONY: maxquit-demo
maxquit-demo:
	@set -e; \
	for q in $(MAX_QUIT_COUNTS); do \
		printf '\n===== %s +max_quit_count=%s =====\n' "$(MAX_QUIT_TEST_FILTER)" "$$q"; \
		$(MAKE) SIM=$(SIM) TOPLEVEL_LANG=$(TOPLEVEL_LANG) \
			COCOTB_TEST_FILTER=$(MAX_QUIT_TEST_FILTER) \
			COCOTB_PLUSARGS="$(COCOTB_PLUSARGS) +max_quit_count=$$q" \
			sim checkclean; \
	done
