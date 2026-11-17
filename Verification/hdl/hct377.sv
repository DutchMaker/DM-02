`timescale 1ns/1ps
// SCHS184C HCT, 4.5 V / -40..85 C / 50 pF, input tr=tf=6 ns.
// reset_n is an observation port, NOT a storage reset or timing-check mask.
module hr1_377 #(parameter real TQ=48,TSU=15,TH=3,TEH=5,TPULSE=25,parameter REQUIRE_INIT=0)
 (input [7:0] d,input clk,enable_n,output [7:0] q,input reset_n);
 reg [7:0] stored;
 reg captured=0,seen_clock=0,seen_fall=0,bad=0,valid_init=0,saw_reset=0;
 real ld=-10000,le=-10000,lc=-10000,lf=-10000;
 real ds=1e9,es=1e9,dh=1e9,eh=1e9,hp=1e9,lp=1e9;
 integer captures=0,reset_captures=0,startup_violations=0;
 task violation(input string reason);
 begin
   if(reset_n===1'b1) $fatal(1,"HR1 %s %m",reason);
   $display("HR1_STARTUP_UNKNOWN %m %s time_ns=%0.3f",reason,$realtime);
   startup_violations=startup_violations+1;bad=1;valid_init=0;stored<=8'bx;
 end
 endtask
 always @(negedge reset_n) begin saw_reset=1;valid_init=0;end
 always @(posedge reset_n) if(REQUIRE_INIT && saw_reset)
   if(!valid_init || $isunknown(stored)) $fatal(1,"HR1 missing synchronous init %m");
 assign #(TQ) q=stored;
 always @(d) begin
   if(seen_clock && captured) begin
     if($realtime-lc<TH) violation("data hold");
     else if($realtime-lc-TH<dh) dh=$realtime-lc-TH;
   end
   ld=$realtime;
 end
 always @(enable_n) begin
   if(seen_clock) begin
     if($realtime-lc<TEH) violation("enable hold");
     else if($realtime-lc-TEH<eh) eh=$realtime-lc-TEH;
   end
   le=$realtime;
 end
 always @(posedge clk) begin
   bad=0;
   if($realtime-le<TSU) violation("enable setup");
   if(enable_n===1'b0 && $realtime-ld<TSU) violation("data setup");
   if(seen_fall && $realtime-lf<TPULSE) violation("low pulse");
   if(!bad && $realtime-le-TSU<es) es=$realtime-le-TSU;
   if(!bad && seen_fall && $realtime-lf-TPULSE<lp) lp=$realtime-lf-TPULSE;
   captured=(enable_n===1'b0 && !bad);
   if(captured) begin
     if($realtime-ld-TSU<ds) ds=$realtime-ld-TSU;
     stored<=d;captures=captures+1;valid_init=1;
     if(reset_n===1'b0) reset_captures=reset_captures+1;
   end else if(enable_n!==1'b1) stored<=8'bx;
   lc=$realtime;seen_clock=1;
 end
 always @(negedge clk) begin
   if(seen_clock) begin
     if($realtime-lc<TPULSE) violation("high pulse");
     else if($realtime-lc-TPULSE<hp) hp=$realtime-lc-TPULSE;
   end
   lf=$realtime;seen_fall=1;
 end
 final $display("HR1_SUMMARY %m captures=%0d reset_captures=%0d startup_violations=%0d data_setup=%0.3f enable_setup=%0.3f data_hold=%0.3f enable_hold=%0.3f high_pulse=%0.3f low_pulse=%0.3f",captures,reset_captures,startup_violations,ds,es,dh,eh,hp,lp);
endmodule
