.PHONY: run_icarus
run_icarus:
	make -C tests/TinyALU SIM=icarus

.PHONY: run_questa
run_questa:
	make -C examples/TinyALU SIM=questa

.PHONY: run_vcs
run_vcs:
	make -C examples/TinyALU SIM=vcs

.PHONY: run_verilator
run_verilator:
	make -C examples/TinyALU SIM=verilator

.PHONY: init
init:
	pip install -r requirements.txt
	pip install -e .

.PHONY: lint
lint:
	@pylint pyuvm

.PHONY: test
pytests:
	pytest tests/pytests

cocotb_tests:
	make -C tests/cocotb_tests/queue sim checkclean
	make -C tests/cocotb_tests/run_phase sim checkclean
	make -C tests/cocotb_tests/decorator sim checkclean
	make -C tests/cocotb_tests/t05_base_classes sim checkclean
	make -C tests/cocotb_tests/t08_factories sim checkclean
	make -C tests/cocotb_tests/t09_phasing sim checkclean
	make -C tests/cocotb_tests/t12_tlm sim checkclean
	make -C tests/cocotb_tests/t13_components sim checkclean
	make -C tests/cocotb_tests/config_db sim checkclean
	make -C tests/cocotb_tests/t14_15_sequences sim checkclean
	make -C tests/cocotb_tests/ext_classes sim checkclean
	make -C examples/TinyALU sim checkclean
	make -C examples/TinyALU_reg sim checkclean
	make SIM=ghdl TOPLEVEL_LANG=vhdl -C examples/TinyALU sim checkclean
