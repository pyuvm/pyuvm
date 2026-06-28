"""End-to-end pyuvm example: a custom UVM agent for a simple memory bus.

This module is intended to be read top-to-bottom as a worked example of
the standard UVM topology, in Python:

    sequence_item  ->  sequence(s)  ->  sequencer  ->  driver  ->  DUT
                                                                    |
                                                       monitor  <---+
                                                          |
                                                  +-------+-------+
                                                  v               v
                                              scoreboard      coverage

Run it with the bundled ``Makefile``:

    cd examples/SimpleMem
    make

Tests cover an ACTIVE agent (driver + monitor) doing random and
write-then-read sequences, and a PASSIVE agent (monitor only) observing
stimulus that is generated outside of UVM.
"""

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from simple_mem_utils import GoldenMem, MemOp, SimpleMemBfm

import pyuvm
from pyuvm import (
    ConfigDB,
    UVMConfigItemNotFound,
    uvm_active_passive_enum,
    uvm_agent,
    uvm_analysis_port,
    uvm_driver,
    uvm_env,
    uvm_get_port,
    uvm_monitor,
    uvm_root,
    uvm_scoreboard,
    uvm_sequence,
    uvm_sequence_item,
    uvm_sequencer,
    uvm_subscriber,
    uvm_test,
    uvm_tlm_analysis_fifo,
)

ADDR_WIDTH = SimpleMemBfm.ADDR_WIDTH
DATA_WIDTH = SimpleMemBfm.DATA_WIDTH
DATA_MASK = (1 << DATA_WIDTH) - 1
ADDR_MASK = (1 << ADDR_WIDTH) - 1


# ---------------------------------------------------------------------------
# Sequence item
# ---------------------------------------------------------------------------


class MemSeqItem(uvm_sequence_item):
    """One bus transaction.

    ``rdata_observed`` is filled by the driver after the DUT responds
    to a READ.
    """

    def __init__(self, name, op=MemOp.READ, addr=0, wdata=0):
        super().__init__(name)
        self.op = MemOp(op)
        self.addr = addr & ADDR_MASK
        self.wdata = wdata & DATA_MASK
        self.rdata_observed = 0

    def randomize(self):
        self.op = random.choice(list(MemOp))
        self.addr = random.randint(0, ADDR_MASK)
        self.wdata = random.randint(0, DATA_MASK)

    def __str__(self):
        if self.op == MemOp.WRITE:
            return f"{self.get_name()} : WRITE @0x{self.addr:02x} = 0x{self.wdata:08x}"
        return (
            f"{self.get_name()} : READ  @0x{self.addr:02x} -> "
            f"0x{self.rdata_observed:08x}"
        )


# ---------------------------------------------------------------------------
# Sequences
# ---------------------------------------------------------------------------


class MemRandomSeq(uvm_sequence):
    """Fire ``count`` transactions through the sequencer.

    The sequence opens with a deterministic warmup that visits every
    ``(op, addr-bucket)`` pair exactly once, then fills the remaining
    ``count - n_directed`` shots with randomised transactions. The
    directed prefix guarantees the coverage subscriber closes on every
    Python / cocotb matrix combination — a pure 32-shot random
    sequence misses ``(WRITE, addr-bucket 2)`` about once every twenty
    runs on Python 3.8 + cocotb 1.8, where the underlying RNG's draw
    order leaves a hole. The random tail still exercises the bus with
    unpredictable address/data patterns so the scoreboard and BFM
    aren't degenerated to a fixed trace.
    """

    BUCKETS = 4  # must mirror MemCoverage.BUCKETS

    def __init__(self, name, count=32):
        super().__init__(name)
        self._count = count

    async def body(self):
        # Directed warmup: hit every (op, addr-bucket) pair once.
        bucket_size = (1 << ADDR_WIDTH) // self.BUCKETS
        n_directed = 0
        for op in MemOp:
            for b in range(self.BUCKETS):
                # Land in the middle of each bucket so future random
                # shots to the bucket boundaries don't get treated as
                # duplicates by the coverage tracker.
                addr = b * bucket_size + (bucket_size // 2)
                item = MemSeqItem(
                    f"warmup_{op.name.lower()}_b{b}",
                    op=op,
                    addr=addr,
                    wdata=0x5A5A_0000 | (op.value << 8) | addr,
                )
                await self.start_item(item)
                await self.finish_item(item)
                n_directed += 1

        # Random tail — preserves the original "32 random shots" feel.
        for i in range(max(0, self._count - n_directed)):
            item = MemSeqItem(f"rand_{i}")
            await self.start_item(item)
            item.randomize()
            await self.finish_item(item)


class MemWriteThenReadSeq(uvm_sequence):
    """Write a pattern across every address, then read every address back.

    Exercises the full address space and forces the scoreboard to predict
    every read.
    """

    async def body(self):
        for addr in range(1 << ADDR_WIDTH):
            wr = MemSeqItem(
                f"wr_{addr:02x}", op=MemOp.WRITE, addr=addr, wdata=0xA5A5_0000 | addr
            )
            await self.start_item(wr)
            await self.finish_item(wr)
        for addr in range(1 << ADDR_WIDTH):
            rd = MemSeqItem(f"rd_{addr:02x}", op=MemOp.READ, addr=addr)
            await self.start_item(rd)
            await self.finish_item(rd)


# ---------------------------------------------------------------------------
# Driver, monitor, sequencer, agent
# ---------------------------------------------------------------------------


class MemDriver(uvm_driver):
    """Pulls items from the sequencer and drives the BFM."""

    def build_phase(self):
        self.bfm = SimpleMemBfm()

    async def run_phase(self):
        # The agent's reset happens before run_phase is entered; nothing to do
        # here at the start except start consuming.
        while True:
            item = await self.seq_item_port.get_next_item()
            rdata = await self.bfm.send(item.op, item.addr, item.wdata)
            item.rdata_observed = rdata
            self.logger.debug(f"DRV {item}")
            self.seq_item_port.item_done()


class MemMonitor(uvm_monitor):
    """Observes accepted bus transactions and publishes them to subscribers."""

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.bfm = SimpleMemBfm()

    async def run_phase(self):
        while True:
            op, addr, wdata, rdata = await self.bfm.get_monitored()
            item = MemSeqItem("mon_item", op=op, addr=addr, wdata=wdata)
            item.rdata_observed = rdata
            self.logger.debug(f"MON {item}")
            self.ap.write(item)


class MemSequencer(uvm_sequencer):
    """Standard sequencer; broken out so tests can locate it by type."""


class MemAgent(uvm_agent):
    """Active agent owns driver + sequencer + monitor; passive owns monitor only.

    ``is_active`` follows the standard UVM pattern: it defaults to
    ``UVM_ACTIVE`` and can be overridden via ``ConfigDB().set(...,
    "is_active", UVM_PASSIVE)`` from the test.
    """

    def build_phase(self):
        super().build_phase()  # populates self.is_active from ConfigDB
        self.monitor = MemMonitor("monitor", self)
        if self.active():
            self.sequencer = MemSequencer("sequencer", self)
            self.driver = MemDriver("driver", self)
            # Publish the sequencer so tests/sequences can find it without
            # threading it through every constructor.
            ConfigDB().set(None, "*", "MEM_SEQR", self.sequencer)

    def connect_phase(self):
        if self.active():
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)


# ---------------------------------------------------------------------------
# Scoreboard + coverage subscribers
# ---------------------------------------------------------------------------


class MemScoreboard(uvm_scoreboard):
    """Predicts read data using a golden memory model.

    Maintains a TLM FIFO of monitored transactions and walks it during
    ``check_phase`` so the result is deterministic at end-of-test.
    """

    def build_phase(self):
        self.fifo = uvm_tlm_analysis_fifo("fifo", self)
        self.port = uvm_get_port("port", self)
        # Exported externally for connection in the env.
        self.analysis_export = self.fifo.analysis_export

    def connect_phase(self):
        self.port.connect(self.fifo.get_export)

    def check_phase(self):
        mem = GoldenMem(size=1 << ADDR_WIDTH)
        passed = True
        seen_any = False
        while self.port.can_get():
            ok, item = self.port.try_get()
            if not ok:
                continue
            seen_any = True
            if item.op == MemOp.WRITE:
                mem.write(item.addr, item.wdata)
            else:
                expected = mem.predict_read(item.addr)
                if item.rdata_observed != expected:
                    self.logger.error(
                        f"FAIL @0x{item.addr:02x}: rdata=0x{item.rdata_observed:08x} "
                        f"expected=0x{expected:08x}"
                    )
                    passed = False
                else:
                    self.logger.info(
                        f"PASS @0x{item.addr:02x}: rdata=0x{item.rdata_observed:08x}"
                    )
        assert seen_any, "scoreboard saw zero transactions"
        assert passed, "scoreboard found a mismatch"


class MemCoverage(uvm_subscriber):
    """Tracks which (op, addr-bucket) pairs were exercised.

    A real environment would use a richer covergroup, but the point here
    is to show where coverage hooks into the analysis fan-out.
    """

    BUCKETS = 4  # split the address space into N equal regions

    def end_of_elaboration_phase(self):
        self._cvg = set()

    def write(self, item):
        bucket = (item.addr * self.BUCKETS) >> ADDR_WIDTH
        self._cvg.add((item.op, bucket))

    def report_phase(self):
        try:
            disable = ConfigDB().get(self, "", "DISABLE_COVERAGE_ERRORS")
        except UVMConfigItemNotFound:
            disable = False
        expected = {(op, b) for op in MemOp for b in range(self.BUCKETS)}
        missing = expected - self._cvg
        if missing and not disable:
            self.logger.error(f"coverage holes: {sorted(missing)}")
            assert False
        self.logger.info(
            f"coverage: hit {len(self._cvg)}/{len(expected)} (op, addr-bucket) pairs"
        )


# ---------------------------------------------------------------------------
# Env + tests
# ---------------------------------------------------------------------------


class MemEnv(uvm_env):
    def build_phase(self):
        # The DUT clock is driven from here so tests don't have to.
        self._clock = Clock(cocotb.top.clk, 10, units="ns")
        cocotb.start_soon(self._clock.start())

        self.agent = MemAgent("agent", self)
        self.scoreboard = MemScoreboard("scoreboard", self)
        self.coverage = MemCoverage("coverage", self)

    def connect_phase(self):
        # Monitor fan-out: every observed transaction reaches scoreboard +
        # coverage, regardless of whether the agent is active or passive.
        self.agent.monitor.ap.connect(self.scoreboard.analysis_export)
        self.agent.monitor.ap.connect(self.coverage.analysis_export)


class _MemTestBase(uvm_test):
    """Shared boilerplate for every Mem* test.

    Brings up the env, resets the DUT, runs a sequence, and asserts
    coverage and scoreboard at the end.
    """

    SEQUENCE_CLS = MemRandomSeq

    def build_phase(self):
        self.env = MemEnv("env", self)

    async def _run_sequence(self):
        seqr = ConfigDB().get(None, "", "MEM_SEQR")
        seq = self.SEQUENCE_CLS("seq")
        await seq.start(seqr)

    async def run_phase(self):
        self.raise_objection("running test")
        bfm = SimpleMemBfm()
        await bfm.reset()
        bfm.start_bfm()
        await self._run_sequence()
        # Let monitored items drain into the fifo before check_phase.
        for _ in range(5):
            await RisingEdge(cocotb.top.clk)
        self.drop_objection("test done")


@pyuvm.test()
class MemRandomTest(_MemTestBase):
    """Random read/write traffic with an ACTIVE agent."""

    SEQUENCE_CLS = MemRandomSeq


@pyuvm.test()
class MemWriteThenReadTest(_MemTestBase):
    """Write the full address space, then read it back.

    Verifies both the DUT (memory contents survive the writes) and the
    scoreboard (the golden model predicts every read).
    """

    SEQUENCE_CLS = MemWriteThenReadSeq


@pyuvm.test()
class MemPassiveAgentTest(_MemTestBase):
    """The agent is reconfigured as PASSIVE.

    Only a monitor exists in UVM-land. Stimulus is driven by a plain
    cocotb coroutine that pokes the BFM directly, simulating a
    third-party stimulus source. The monitor / scoreboard / coverage
    should still cover every (op, addr-bucket) pair.
    """

    def build_phase(self):
        ConfigDB().set(
            None, "*.agent", "is_active", uvm_active_passive_enum.UVM_PASSIVE
        )
        super().build_phase()

    async def _run_sequence(self):
        bfm = SimpleMemBfm()
        bucket_size = (1 << ADDR_WIDTH) // MemCoverage.BUCKETS
        # Hit one write and one read in every coverage bucket. The point
        # is to demonstrate that the monitor + analysis fan-out still
        # works without any driver under UVM control.
        for bucket in range(MemCoverage.BUCKETS):
            base = bucket * bucket_size
            wr_data = 0xDEAD_0000 | base
            await bfm.send(MemOp.WRITE, base, wr_data)
            await bfm.send(MemOp.READ, base, 0)
        uvm_root().logger.info("passive-agent stimulus complete")


@pyuvm.test(expect_fail=True)
class MemPassiveFailingTest(MemPassiveAgentTest):
    """Negative twin of :class:`MemPassiveAgentTest`.

    Only writes are issued, so the coverage subscriber must flag the
    missing READ buckets. Marked ``expect_fail=True`` so ``make`` still
    exits 0.
    """

    async def _run_sequence(self):
        bfm = SimpleMemBfm()
        bucket_size = (1 << ADDR_WIDTH) // MemCoverage.BUCKETS
        for bucket in range(MemCoverage.BUCKETS):
            base = bucket * bucket_size
            await bfm.send(MemOp.WRITE, base, 0xCAFE_0000 | base)
        uvm_root().logger.info("passive-agent write-only stimulus complete")
