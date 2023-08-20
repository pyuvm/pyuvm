module tinyalu (input [7:0] A,
		input [7:0] B,
		input [2:0] op,
		input clk,
		input reset_n,
		input start,
		output done,
		output [15:0] result,
    // Register Bus
    input  logic valid,    //! Active high valid
    input  logic read,     //! Indicates request is a read
    input  logic [31:0] addr,     //! Address (byte aligned, absolute address)
    /* verilator lint_off UNUSED */
    input  logic [31:0] wdata,    //! Write data
    input  logic [3:0] wmask,    //! Write mask
    /* verilator lint_on UNUSED */
    output logic [31:0] rdata     //! Read data
		);

    localparam ADDR_WIDTH = 32;
    localparam DATA_WIDTH = 32;
    localparam ADDR_OFFSET = 'd0;
    localparam RESERVED_VALUE = 'd1;

    wire [15:0] 		      result_aax, result_mult;
    wire 		          start_single, start_mult;
    wire                   done_aax;
    wire                   done_mult;

    // Register CMD input
    logic       CMD_op_we;             //! Control HW write (active high)
    logic [4:0] CMD_op_wdata;          //! HW write data
    logic       CMD_start_we;             //! Control HW write (active high)
    logic [0:0] CMD_start_wdata;          //! HW write data
    logic       CMD_done_we;             //! Control HW write (active high)
    logic [0:0] CMD_done_wdata;          //! HW write data
    logic       CMD_reserved_we;             //! Control HW write (active high)
    logic [6:0] CMD_reserved_wdata;          //! HW write data
    // Register CMD output
    logic [6:0] CMD_reserved_q;              //! Current field value
    logic [4:0] CMD_op_q;              //! Current field value
    logic [0:0] CMD_start_q;              //! Current field value
    logic [0:0] CMD_done_q;              //! Current field value

    // Register SRC
    logic [7:0] SRC_data0_wdata;          //! HW write data
    logic [7:0] SRC_data1_wdata;          //! HW write data

    // Register RESULT
    logic [15:0] RESULT_data_wdata;          //! HW write data

    assign start_single = start & ~op[2];
    assign start_mult   = start & op[2];

    single_cycle and_add_xor (.A, .B, .op, .clk, .reset_n, .start(start_single),
	   	     .done(done_aax), .result(result_aax));

    three_cycle mult (.A, .B, .op, .clk, .reset_n, .start(start_mult),
	       .done(done_mult), .result(result_mult));

    assign done = (op[2]) ? done_mult : done_aax;

    assign result = (op[2]) ? result_mult : result_aax;

    // Enable write to register from hardware
    assign CMD_op_we = 1'b1;             //! Control HW write (active high)
    assign CMD_start_we = 1'b1;             //! Control HW write (active high)
    assign CMD_done_we = 1'b1;             //! Control HW write (active high)
    assign CMD_reserved_we = 1'b1;             //! Control HW write (active high)
    assign CMD_op_wdata = {2'd0,op};          //! HW write data
    assign CMD_start_wdata = start;          //! HW write data
    assign CMD_done_wdata = done;          //! HW write data
    assign CMD_reserved_wdata = RESERVED_VALUE;          //! HW write data
    assign SRC_data0_wdata = A;
    assign SRC_data1_wdata = B;
    assign RESULT_data_wdata = result;

    TinyALUreg #(
      .ADDR_OFFSET(ADDR_OFFSET),  //! Module's offset in the main address map
      .ADDR_WIDTH (ADDR_WIDTH),   //! Width of SW address bus
      .DATA_WIDTH (ADDR_WIDTH)    //! Width of SW data bus
    )regblock(
      // Clocks and resets
      .clk                (clk),                      //! Default clock
      .resetn             (reset_n),                  //! Default reset
      .SRC_data0_wdata    (SRC_data0_wdata),          //! HW write data
      .SRC_data1_wdata    (SRC_data1_wdata),          //! HW write data
      .RESULT_data_wdata  (RESULT_data_wdata),        //! HW write data
      .CMD_op_we          (CMD_op_we),                //! Control HW write (active high)
      .CMD_op_wdata       (CMD_op_wdata),             //! HW write data
      .CMD_op_q           (CMD_op_q),                 //! Current field value
      .CMD_start_we       (CMD_start_we),             //! Control HW write (active high)
      .CMD_start_wdata    (CMD_start_wdata),          //! HW write data
      .CMD_start_q        (CMD_start_q),              //! Current field value
      .CMD_done_we        (CMD_done_we),              //! Control HW write (active high)
      .CMD_done_wdata     (CMD_done_wdata),           //! HW write data
      .CMD_done_q         (CMD_done_q),               //! Current field value
      .CMD_reserved_we    (CMD_reserved_we),          //! Control HW write (active high)
      .CMD_reserved_wdata (CMD_reserved_wdata),       //! HW write data
      .CMD_reserved_q     (CMD_reserved_q),           //! Current field value
      .valid              (valid),                    //! Active high valid
      .read               (read),                     //! Indicates request is a read
      .addr               (addr),                     //! Address (byte aligned, absolute address)
      .wdata              (wdata),                    //! Write data
      .wmask              (wmask),                    //! Write mask
      .rdata              (rdata)                     //! Read data
    );

endmodule // tinyalu


module single_cycle(input [7:0] A,
		   input [7:0] B,
		   input [2:0] op,
		   input clk,
		   input reset_n,
		   input start,
		   output logic done,
		   output logic [15:0] result);

  always @(posedge clk)
    if (!reset_n)
      result <= 0;
    else
      case(op)
		3'b001 : result <= {8'd0,A} + {8'd0,B};
		3'b010 : result <= {8'd0,A} & {8'd0,B};
		3'b011 : result <= {8'd0,A} ^ {8'd0,B};
		default : result <= {A,B};
      endcase // case (op)

   always @(posedge clk)
     if (!reset_n)
       done <= 0;
     else
       done <= ((start == 1'b1) && (op != 3'b000));

endmodule : single_cycle


module three_cycle(input [7:0] A,
		   input [7:0] B,
		   input [2:0] op,
		   input clk,
		   input reset_n,
		   input start,
		   output logic done,
		   output logic [15:0] result);

   logic [7:0] 			       a_int, b_int;
   logic [15:0] 		       mult1, mult2;
   logic 			       done1, done2, done3;

   always @(posedge clk)
     if (!reset_n) begin
	done  <= 0;
	done3 <= 0;
	done2 <= 0;
	done1 <= 0;
	a_int <= 0;
	b_int <= 0;
	mult1 <= 0;
	mult2 <= 0;
	result<= 0;
     end else begin // if (!reset_n)
	a_int  <= A;
	b_int  <= B;
	mult1  <= a_int * b_int;
	mult2  <= mult1;
	result <= mult2;
	done3  <= start & !done;
	done2  <= done3 & !done;
	done1  <= done2 & !done;
	done   <= done1 & !done;
     end // else: !if(!reset_n)

endmodule : three_cycle
