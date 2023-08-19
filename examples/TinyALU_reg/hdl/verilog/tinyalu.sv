import TinyALUreg_pkg::*;

module tinyalu (input [7:0] A,
		input [7:0] B,
		input [2:0] op,
		input clk,
		input reset_n,
		input start,
		output done,
		output [15:0] result,
    // cpuif
    input wire cpuif_req,
    input wire cpuif_req_is_wr,
    input wire [2:0] cpuif_addr,
    input wire [15:0] cpuif_wr_data,
    input wire [15:0] cpuif_wr_biten,
    output wire cpuif_req_stall_wr,
    output wire cpuif_req_stall_rd,
    output wire cpuif_rd_ack,
    output wire cpuif_rd_err,
    output wire [15:0] cpuif_rd_data,
    output wire cpuif_wr_ack,
    output wire cpuif_wr_err,
		);

   wire [15:0] 		      result_aax, result_mult;
   wire 		          start_single, start_mult;
   wire                   done_aax;
   wire                   done_mult;
   // bit                    clk;
   TinyALUreg__in_t  reg_in;
   TinyALUreg__out_t reg_out;

   // initial clk = 0;
   // always #5 clk = ~clk;

   assign start_single = start & ~op[2];
   assign start_mult   = start & op[2];

   single_cycle and_add_xor (.A, .B, .op, .clk, .reset_n, .start(start_single),
			     .done(done_aax), .result(result_aax));

   three_cycle mult (.A, .B, .op, .clk, .reset_n, .start(start_mult),
		    .done(done_mult), .result(result_mult));


   assign done = (op[2]) ? done_mult : done_aax;

   assign result = (op[2]) ? result_mult : result_aax;

   assign reg_in.SRC.data0.next = A;
   assign reg_in.SRC.data1.next = B;
   assign reg_in.CMD.op.next = op;
   assign reg_in.RESULT.data.next = result;
   assign reg_in.CMD.done.next = done;
   assign reg_in.CMD.start.next = start;
   assign reg_in.CMD.reserved.next = '0;


  TinyALUreg regblock(
    .clk                  (clk),
    .rst                  (reset_n),
    .s_cpuif_req          (cpuif_req),
    .s_cpuif_req_is_wr    (cpuif_req_is_wr),
    .s_cpuif_addr         (cpuif_addr),
    .s_cpuif_wr_data      (cpuif_wr_data),
    .s_cpuif_wr_biten     (cpuif_wr_biten),
    .s_cpuif_req_stall_wr (cpuif_req_stall_wr),
    .s_cpuif_req_stall_rd (cpuif_req_stall_rd),
    .s_cpuif_rd_ack       (cpuif_rd_ack),
    .s_cpuif_rd_err       (cpuif_rd_err),
    .s_cpuif_rd_data      (cpuif_rd_data),
    .s_cpuif_wr_ack       (cpuif_wr_ack),
    .s_cpuif_wr_err       (cpuif_wr_err),
    .hwif_in              (reg_in),
    .hwif_out             (reg_out)
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
