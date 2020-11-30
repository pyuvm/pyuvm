init:
	pip install -r requirements.txt

test:
	nosetests tests

run_nosim:
	python tinyalu_example/no_sim_alu_test.py

run_icarus:
	echo Not Implemented Yet

run_questa:
	echo Not Implemented Yet
