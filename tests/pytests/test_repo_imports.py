"""Issue #406: the repo top is on the test PYTHONPATH.

Any test in the repo should be able to pull code from any other test or
example, e.g. `from examples.TinyALU.testbench import ...`. This test locks
that namespace-package import path in place.
"""

from examples.TinyALU.testbench import Ops as TinyAluOps
from examples.TinyALU.tinyalu_utils import Ops, alu_prediction


def test_cross_test_import_via_repo_namespace():
    assert TinyAluOps.ADD == 1


def test_cross_test_import_of_shared_utils():
    assert Ops.MUL == 4
    assert alu_prediction(5, 3, Ops.ADD) == 8
