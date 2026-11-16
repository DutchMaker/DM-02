`timescale 1ns/1ps
module cp273 #(parameter real TQ=42,TH=3)(input [7:0] d,input clk,clear_n,output [7:0] q);
 reg [7:0] stored;real ld=-10000,lc=-10000,lf=-10000,lr=-10000,la=-10000;
 real minimum_data_hold=1.0e9;integer hold_events=0;
 assign #(TQ) q=stored;
 always @(d) begin
   if(clear_n && lc>=0) begin
     if($realtime-lc<minimum_data_hold) minimum_data_hold=$realtime-lc;
     hold_events=hold_events+1;
     if($realtime-lc<TH) $fatal(1,"CP273 data hold %m");
   end
   ld=$realtime;
 end
 final $display("CP273 hold %m events=%0d minimum_ns=%0.3f",hold_events,minimum_data_hold);
 always @(negedge clk) begin
   if(clear_n && $realtime-lc<25) $fatal(1,"CP273 clock high pulse %m");lf=$realtime;
 end
 always @(negedge clear_n) la=$realtime;
 always @(posedge clear_n) begin
   if($realtime-la<20) $fatal(1,"CP273 clear pulse %m");lr=$realtime;
 end
 always @(posedge clk or negedge clear_n) begin
   if(!clear_n) stored<=0;
   else begin
     if($realtime-ld<25 || $realtime-lr<25) $fatal(1,"CP273 setup/recovery %m");
     if($realtime-lf<25) $fatal(1,"CP273 clock pulse %m");
     stored<=d;lc=$realtime;
   end
 end
endmodule