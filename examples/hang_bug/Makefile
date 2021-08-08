CWD=$(shell pwd)
COCOTB_REDUCED_LOG_FMT = True
SIM ?= icarus
VERILOG_SOURCES =$(CWD)/hdl/clock.sv
MODULE := hanger
TOPLEVEL := clock
COCOTB_HDL_TIMEUNIT=1us
COCOTB_HDL_TIMEPRECISION=1us
include $(shell cocotb-config --makefiles)/Makefile.sim
