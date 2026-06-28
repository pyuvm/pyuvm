// SimpleMem: a tiny synchronous memory with a req/gnt handshake.
//
//   Master drives                Slave responds
//   ─────────────                ──────────────
//   req                          gnt
//   we    (1 = write, 0 = read)  rdata (read transactions only)
//   addr
//   wdata
//
// Single-cycle handshake: when (req && gnt) is high on a rising edge, the
// transaction completes that cycle. Writes are committed in the same cycle.
// Reads return `rdata` in the same cycle (combinational read).
//
// This DUT is intentionally minimal — the point of the example is the UVM
// agent that drives it, not the DUT itself.
module simple_mem #(
    parameter int ADDR_WIDTH = 8,
    parameter int DATA_WIDTH = 32
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    req,
    input  wire                    we,
    input  wire [ADDR_WIDTH-1:0]   addr,
    input  wire [DATA_WIDTH-1:0]   wdata,
    output wire                    gnt,
    output wire [DATA_WIDTH-1:0]   rdata
);

    localparam int DEPTH = 1 << ADDR_WIDTH;

    logic [DATA_WIDTH-1:0] mem [DEPTH];

    // The slave is always ready. This keeps the handshake side of the test
    // boring on purpose so the example focuses on UVM-side machinery.
    assign gnt = req;

    // Combinational read.
    assign rdata = mem[addr];

    // Synchronous write.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < DEPTH; i++) begin
                mem[i] <= '0;
            end
        end else if (req && we) begin
            mem[addr] <= wdata;
        end
    end

endmodule
