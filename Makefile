run_icarus:
	make -C examples/tinyalu/tests

run_nosim:
	python examples/tinyalu/tests/no_sim_alu_test.py

run_questa:
	echo Not Implemented Yet

init:
	pip install -r requirements.txt

test:
	nosetests tests

