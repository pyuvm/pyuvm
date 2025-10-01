import sys

from peakrdl.verilog import VerilogExporter
from systemrdl import RDLCompileError, RDLCompiler

rdlc = RDLCompiler()

try:
    rdlc.compile_file("./TinyALUreg.rdl")
    root = rdlc.elaborate()
except RDLCompileError:
    sys.exit(1)

exporter = VerilogExporter()
exporter.export(root, "./hdl/verilog/")
