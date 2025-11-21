// AOI (AND-OR-INVERT) Module for Basys3 Board
// Filename: aoi_2_2.v
// Implements: Y = ~((A & B) | (C & D))
// Maps to Basys3 switches and 7-segment display

module aoi_2_2 (
    input  wire [3:0] SWT,      // 4 switches: SWT[3:0] for inputs a,b,c,d
    output wire [6:0] SEG,       // 7-segment display segments
    output wire [3:0] AN         // 7-segment display anodes (digit enable)
);

    // Internal signals
    wire a, b, c, d;
    wire y;

    // Map switches to inputs
    assign a = SWT[0];
    assign b = SWT[1];
    assign c = SWT[2];
    assign d = SWT[3];

    // AOI logic: NOT of ((A AND B) OR (C AND D))
    assign y = ~((a & b) | (c & d));

    // Enable only the rightmost digit (AN[0])
    assign AN = 4'b1110;  // Active low, so 0 enables digit 0

    // Display output on 7-segment display
    // Show '0' if y=0, show '1' if y=1
    // 7-segment encoding: {g, f, e, d, c, b, a}
    // Display is active low (0 = segment ON)
    assign SEG = (y == 1'b0) ? 7'b1000000 : 7'b1111001;   // Display '0' or '1'

endmodule
