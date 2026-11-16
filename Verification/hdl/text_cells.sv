`timescale 1ns/1ps
// Digital timing observations only. No metastability or analog output model.
module tx_watch #(parameter W=1,SETUP=0,HOLD=0,REC=0,PULSE=0,CHECK=1)
 (input clk,reset_n,input [W-1:0] data);
 real changed=-1e9,captured=-1e9,released=-1e9,edge_time=-1e9;
 integer violations=0; real min_setup=1e9,min_hold=1e9;
 always @(data) begin
   if(reset_n && $realtime-captured<min_hold)min_hold=$realtime-captured;
   if(CHECK && reset_n && $realtime-captured<HOLD)begin
     violations=violations+1;$display("TIMING hold %m interval=%0.3f",$realtime-captured);
   end
   changed=$realtime;
 end
 always @(posedge reset_n) released=$realtime;
 always @(clk) begin
   if(CHECK && reset_n && $realtime-edge_time<PULSE)begin
     violations=violations+1;$display("TIMING pulse %m interval=%0.3f",$realtime-edge_time);
   end
   edge_time=$realtime;
 end
 always @(posedge clk) if(reset_n)begin
   if($realtime-changed<min_setup)min_setup=$realtime-changed;
   if(CHECK && ($realtime-changed<SETUP || $realtime-released<REC))begin
     violations=violations+1;$display("TIMING setup/recovery %m setup=%0.3f recovery=%0.3f",$realtime-changed,$realtime-released);
   end
   captured=$realtime;
 end
 final $display("TIMING_SUMMARY %m violations=%0d setup_ns=%0.3f hold_ns=%0.3f checked=%0d",violations,min_setup,min_hold,CHECK);
endmodule

module tx_ff #(parameter T=0,CHECK=1)(input d,clk,clear_n,preset_n,output q,qn);
 reg value;
 always @(posedge clk or negedge clear_n or negedge preset_n)
   if(!clear_n && !preset_n)value<=1'bx;
   else if(!clear_n)value<=0;else if(!preset_n)value<=1;else value<=d;
 assign #(T) q=value;assign #(T) qn=~value;
 tx_watch #(1,15,3,8,23,CHECK) watch(clk,clear_n & preset_n,d);
endmodule

module tx_reg #(parameter T=0,CHECK=1)(input [7:0] d,input clk,clear_n,output [7:0] q);
 reg [7:0] value;
 always @(posedge clk or negedge clear_n)if(!clear_n)value<=0;else value<=d;
 assign #(T) q=value;
 tx_watch #(8,25,3,25,25,CHECK) watch(clk,clear_n,d);
endmodule

module tx_count #(parameter T=0,CHECK=1)(input [3:0] d,input clk,clear_n,load_n,pe,te,
 output [3:0] q,output tc);
 reg [3:0] value;
 always @(posedge clk or negedge clear_n)
   if(!clear_n)value<=0;else if(!load_n)value<=d;else if(pe && te)value<=value+1'b1;
 assign #(T) q=value;assign #(T) tc=te && (&value);
 tx_watch #(7,16,5,19,25,CHECK) watch(clk,clear_n,{d,load_n,pe,te});
endmodule
