from enum import Enum, auto, unique

'''
9.1
The UVM Specification specifies a generalized phasing solution.  Reimplementing
this for Python is left as a future exercise.

This system works only with the basic UVM phases and uses Enums to standardize
names and directions. 
'''


@unique
class PhaseType ( Enum ):
    TOPDOWN = auto ()
    BOTTOMUP = auto ()
    TASK=auto()

@unique
class PyuvmPhases ( Enum ):

    BUILD = ('build_phase', PhaseType.TOPDOWN)
    CONNECT=('connect_phase', PhaseType.BOTTOMUP)
    END_OF_ELABORATION=('end_of_elaboration_phase', PhaseType.BOTTOMUP)
    START_OF_SIMULATION=('start_of_simulation_phase', PhaseType.BOTTOMUP)
    RUN=('run_phase', PhaseType.TASK)
    EXTRACT=('extract_phase', PhaseType.BOTTOMUP)
    CHECK=('check_phase', PhaseType.BOTTOMUP)
    REPORT=('report_phase',PhaseType.BOTTOMUP)
    FINAL=('final_phase',PhaseType.TOPDOWN)
