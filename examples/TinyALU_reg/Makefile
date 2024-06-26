CWD=$(shell pwd)
export COCOTB_REDUCED_LOG_FMT = 1
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
ifeq ($(TOPLEVEL_LANG),verilog)
	VERILOG_SOURCES =$(CWD)/hdl/verilog/tinyalu.sv $(CWD)/hdl/verilog/TinyALUreg.sv
else ifeq ($(TOPLEVEL_LANG),vhdl)
	VHDL_SOURCES=$(CWD)/hdl/vhdl/single_cycle_add_and_xor.vhd \
				$(CWD)/hdl/vhdl/three_cycle_mult.vhd \
				$(CWD)/hdl/vhdl/tinyalu.vhd
else
    $(error "A valid value (verilog or vhdl) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG)")
endif
ifeq ($(SIM), verilator)
    # Enable processing of #delay statements
    COMPILE_ARGS += --timing
	EXTRA_ARGS += --trace --trace-structs
endif
MODULE := testbench
TOPLEVEL = tinyalu
GHDL_ARGS := --ieee=synopsys
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps
include $(shell cocotb-config --makefiles)/Makefile.sim
include ../../checkclean.mk