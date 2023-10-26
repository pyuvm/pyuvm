import sys
from systemrdl import RDLCompiler, RDLCompileError
from peakrdl.verilog import VerilogExporter

rdlc = RDLCompiler()

try:
    rdlc.compile_file("./TinyALUreg.rdl")
    root = rdlc.elaborate()
except RDLCompileError:
    sys.exit(1)

exporter = VerilogExporter()
exporter.export(root, "./hdl/verilog/")
