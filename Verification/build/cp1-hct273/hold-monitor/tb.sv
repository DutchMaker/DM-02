`timescale 1ns/1ps
module tb;
 parameter real GAP=4,HOLD=3;
 reg [7:0] d=0;reg clk=0,clear_n=1;wire [7:0] q;
 cp273 #(42,HOLD) dut(d,clk,clear_n,q);
 initial begin #1;clear_n=0;#30;clear_n=1;#30;clk=1;#(GAP);d=1;#30;clk=0;#50;$display("DONE hold fixture");$finish;end
endmodule
