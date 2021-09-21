run_icarus:
	make -C tests/cocotb SIM=icarus

run_questa:
	make -C examples/tinyalu/tests SIM=questa

init:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/nosetests

