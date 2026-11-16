`timescale 1ns/1ps
// Timing-table models at 4.5 V, -40..85 C. No assumed power-on zero state.
// CD74HCT273E: SCHS174D clock/clear maxima 38/40 ns at 4.5 V,
// -40..85 C and 50 pF. Retain the conservative CP1 42 ns envelope.
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

module cp191 #(parameter real TQ=34,TRCO=44,TTC=53,TLOAD=50,TDATA=48)
 (input [3:0] d,input clk,load_n,ce_n,down,output [3:0] q,output tc,rco_n,input reset_n);
 reg [3:0] stored;real ld=-10000,le=-10000,lu=-10000,lc=-10000,lf=-10000,ll=-10000,lr=-10000;
 // TC is a count-state output; RCO is low only during clock-low at terminal count.
 wire terminal=down ? stored==0 : &stored;
 localparam real TOUT=(TQ>TLOAD ? (TQ>TDATA ? TQ : TDATA) : (TLOAD>TDATA ? TLOAD : TDATA));
 assign #(TOUT) q=stored;
 assign #(TTC) tc=terminal;
 assign #(TRCO) rco_n=~(!ce_n && !clk && terminal);
 always @(d) begin
   if(reset_n && $realtime-lr<2) $fatal(1,"CP191 data hold after LOAD %m");ld=$realtime;
 end
 always @(ce_n) begin
   if(reset_n && $realtime-lc<2) $fatal(1,"CP191 enable hold %m");
   if(reset_n && clk===0) $fatal(1,"CP191 enable changed with low clock %m");le=$realtime;
 end
 always @(down) begin
   if(reset_n && clk===0) $fatal(1,"CP191 direction changed with low clock %m");lu=$realtime;
 end
 always @(negedge load_n) ll=$realtime;
 always @(posedge load_n) begin
   if(reset_n && ($realtime-ll<20 || $realtime-ld<15)) $fatal(1,"CP191 load pulse/data setup %m");lr=$realtime;
 end
 always @(negedge clk) begin
   if(reset_n && $realtime-lc<25) $fatal(1,"CP191 clock high pulse %m");lf=$realtime;
 end
 always @(load_n or d) if(!load_n) stored<=d;
 always @(posedge clk) begin
   if(reset_n && load_n) begin
     if($realtime-lf<25 || $realtime-lr<15) $fatal(1,"CP191 clock pulse/load recovery %m");
     if($realtime-le<15 || $realtime-lu<23) $fatal(1,"CP191 count setup %m");
   end
   if(load_n && !ce_n) stored<=down ? stored-1'b1 : stored+1'b1;
   lc=$realtime;
 end
endmodule

module cp_control_rom #(parameter real TACC=100)(input [15:0] address,input ce_n,oe_n,output [15:0] q);
 reg [15:0] memory[0:65535],value;integer generation=0;
 initial $readmemh("control.hex",memory);
 assign q=value;
 task automatic resolve(input integer token,input [15:0] a,input ce,oe);
 begin #(TACC);if(token==generation) value=(ce || oe) ? 16'bz : memory[a];end
 endtask
 always @(address or ce_n or oe_n) begin
   generation=generation+1;value=16'bx;
   fork resolve(generation,address,ce_n,oe_n);join_none
 end
endmodule
