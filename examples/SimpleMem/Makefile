CWD = $(shell pwd)

export COCOTB_REDUCED_LOG_FMT = 1

SIM           ?= icarus
TOPLEVEL_LANG ?= verilog
TOPLEVEL       = simple_mem
MODULE        := testbench

VERILOG_SOURCES = $(CWD)/hdl/verilog/simple_mem.sv

COCOTB_HDL_TIMEUNIT      = 1ns
COCOTB_HDL_TIMEPRECISION = 1ns

ifeq ($(SIM), verilator)
    # Enable processing of #delay statements
    COMPILE_ARGS += --timing
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
include ../../checkclean.mk
