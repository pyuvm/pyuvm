CWD=$(shell pwd)
export COCOTB_REDUCED_LOG_FMT = 1
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

ifeq ($(TOPLEVEL_LANG),verilog)
	# Check multiple possible locations for the Verilog file
	ifneq ("$(wildcard $(CWD)/hdl/verilog/aoi_2_2.v)","")
		VERILOG_SOURCES = $(CWD)/hdl/verilog/aoi_2_2.v
	else ifneq ("$(wildcard $(CWD)/aoi_2_2.v)","")
		VERILOG_SOURCES = $(CWD)/aoi_2_2.v
	else
		$(error "Cannot find aoi_2_2.v in $(CWD) or $(CWD)/hdl/verilog/")
	endif
else ifeq ($(TOPLEVEL_LANG),vhdl)
	# Check multiple possible locations for the VHDL file
	ifneq ("$(wildcard $(CWD)/hdl/vhdl/aoi_2_2.vhd)","")
		VHDL_SOURCES = $(CWD)/hdl/vhdl/aoi_2_2.vhd
	else ifneq ("$(wildcard $(CWD)/aoi_2_2.vhd)","")
		VHDL_SOURCES = $(CWD)/aoi_2_2.vhd
	else
		$(error "Cannot find aoi_2_2.vhd in $(CWD) or $(CWD)/hdl/vhdl/")
	endif
else
    $(error "A valid value (verilog or vhdl) was not provided for TOPLEVEL_LANG=$(TOPLEVEL_LANG)")
endif

# Verilator specific settings
ifeq ($(SIM), verilator)
    # Enable processing of #delay statements
    COMPILE_ARGS += --timing
    # Enable coverage collection
    COMPILE_ARGS += --coverage --coverage-line --coverage-toggle
    EXTRA_ARGS += --coverage
endif

# Use COCOTB_TEST_MODULES instead of deprecated MODULE
COCOTB_TEST_MODULES := testbench
TOPLEVEL := aoi_2_2

# GHDL specific arguments (only used if SIM=ghdl)
GHDL_ARGS := --ieee=synopsys

# Enable coverage for GHDL (optional - only works with gcc/llvm backend, not mcode)
# Uncomment the following lines if you have GHDL with gcc or llvm backend:
# ifeq ($(SIM), ghdl)
#     COMPILE_ARGS += -fcover=stmt,branch,toggle
#     SIM_ARGS += --coverage
# endif

# Time unit settings
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

include $(shell cocotb-config --makefiles)/Makefile.sim

# Optional: include checkclean if it exists
-include ../../checkclean.mk

# Coverage report generation targets
.PHONY: coverage coverage-report

coverage: sim
	@echo "Running simulation with coverage enabled..."

coverage-report:
	@if [ -f "coverage.dat" ]; then \
		echo "Generating coverage report..."; \
		verilator_coverage --annotate coverage_html coverage.dat; \
		verilator_coverage --write-info coverage.info coverage.dat; \
		echo "Coverage report generated in coverage_html/"; \
		echo "Open coverage_html/index.html in your browser"; \
	else \
		echo "Error: coverage.dat not found. Run 'make clean && make sim SIM=verilator' first"; \
	fi
