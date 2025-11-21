#!/bin/bash
################################################################################
# Profile cocotb simulation
################################################################################

echo "Running simulation with profiling..."
echo ""

# Clean previous runs
make clean

# Run with Python profiler
python3 -m cProfile -o simulation_profile.pstat \
    -m cocotb.runner \
    --toplevel aoi_2_2 \
    --module testbench \
    --waves || \
    echo "Note: cocotb.runner not available, trying make..."
    make sim SIM=verilator

# Check if profile was created
if [ -f "simulation_profile.pstat" ]; then
    echo ""
    echo "Profile generated: simulation_profile.pstat"
    echo "Analyzing..."
    echo ""
    python3 analyze_profile.py simulation_profile.pstat
elif [ -f "profile.pstat" ]; then
    echo ""
    echo "Profile generated: profile.pstat"
    echo "Analyzing..."
    echo ""
    python3 analyze_profile.py profile.pstat
else
    echo ""
    echo "No profile file generated."
    echo "Your cocotb version may not support COCOTB_ENABLE_PROFILING"
    echo "Cocotb version: $(python3 -c 'import cocotb; print(cocotb.__version__)')"
    echo ""
    echo "Alternative: Use Python's line_profiler or kernprof instead"
fi
