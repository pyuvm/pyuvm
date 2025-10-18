CWD=$(shell pwd)
COCOTB_REDUCED_LOG_FMT = True
SIM ?= icarus
VERILOG_SOURCES =$(CWD)/clk.sv
COCOTB_TEST_MODULES := test
# INFO: Backward compatibility for Cocotb <= 1.9
MODULE := $(COCOTB_TEST_MODULES)
TOPLEVEL := clocker
TOPLEVEL_LANG=verilog
COCOTB_HDL_TIMEUNIT=1us
COCOTB_HDL_TIMEPRECISION=1us
include $(shell cocotb-config --makefiles)/Makefile.sim
include ../../../checkclean.mk
