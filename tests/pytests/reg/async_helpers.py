import asyncio


def run_pytest_coro(coro):
    """Run an isolated Python coroutine from a pure pytest unit test.

    cocotb tests run on the cocotb scheduler. These RAL unit tests use local
    fakes and no simulator triggers, so asyncio is only the pytest harness.
    """
    return asyncio.run(coro)
