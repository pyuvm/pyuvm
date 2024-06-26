check:
	../combine_results.py

testclean: clean
	@rm -rf __pycache__
	@rm -rf results.xml
	@rm -rf combined_results.xml
	@rm -rf log.txt
	@rm -rf sim_build
	@rm -rf modelsim.ini
	@rm -rf transcript

checkclean: check testclean

