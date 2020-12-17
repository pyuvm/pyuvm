run_icarus:
	make -C examples/tinyalu/tests SIM=icarus

run_nosim:
	python examples/tinyalu/tests/no_sim_alu_test.py

run_questa:
	make -C examples/tinyalu/tests SIM=questa


init:
	pip install -r requirements.txt

test:
	nosetests tests

