run_icarus:
	make -C tinyalu_example/tests

run_nosim:
	python tinyalu_example/tests/no_sim_alu_test.py

run_questa:
	echo Not Implemented Yet

init:
	pip install -r requirements.txt

test:
	nosetests tests

