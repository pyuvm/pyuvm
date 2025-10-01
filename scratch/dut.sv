// -------------------------------------------------------------------
// @author raysalemi
// @copyright (C) 2020, <COMPANY>
//
// Created : 03. Dec 2020 8:25 AM
//-------------------------------------------------------------------
module dut(input bit clk,
input bit reset_n, input int unsigned data_in, output int unsigned data_out);
    always @(posedge clk)
        if (reset_n == 0)
            begin
                $display("reseting");
                data_out <= 0;
            end
        else
            begin
                data_out <= data_in;
            end

    always @(data_in)
          $display("data_in: %0d", data_in);

    always @(data_out)
          $display("data_out: %0d", data_out);

endmodule : dut
