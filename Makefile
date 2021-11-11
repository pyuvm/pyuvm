run_icarus:
	make -C tests/cocotb SIM=icarus

run_questa:
	make -C examples/TinyALU SIM=questa

run_vcs:
	make -C examples/TinyALU SIM=vcs

init:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/pytests

