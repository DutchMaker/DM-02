module cw_rom #(parameter real TACC=0,parameter FILE="low.hex")
 (input [15:0] a,input ce_n,oe_n,output [7:0] q);
 reg [7:0] memory[0:65535];reg [7:0] value;integer generation=0;
 initial $readmemh(FILE,memory);
 assign q=value;
 task automatic resolve(input integer token,input [15:0] address,input ce,oe);
 begin
   #(TACC);
   if(generation==token) value=(ce || oe) ? 8'bz : memory[address];
 end
 endtask
 // Zero contamination bound is conservative even though the ROM specifies 7 ns hold.
 always @(a or ce_n or oe_n) begin
   generation=generation+1;value=8'bx;
   fork resolve(generation,a,ce_n,oe_n); join_none
 end
endmodule

module cw574 #(parameter real TQ=45,TSU=25,TH=5,TPULSE=20)
 (input [7:0] d,input clk,oe_n,output [7:0] q,input reset_n);
 reg [7:0] stored;real ld=-10000,lc=-10000,lf=-10000;
 assign #(TQ) q=oe_n ? 8'bz : stored;
 always @(d) begin
   if(reset_n && $realtime-lc<TH) $fatal(1,"CW data hold %m");
   ld=$realtime;
 end
 always @(posedge clk) begin
   if(reset_n && $realtime-ld<TSU) $fatal(1,"CW data setup %m");
   if(reset_n && $realtime-lf<TPULSE) $fatal(1,"CW low pulse %m");
   stored<=d;lc=$realtime;
 end
 always @(negedge clk) begin
   if(reset_n && $realtime-lc<TPULSE) $fatal(1,"CW high pulse %m");
   lf=$realtime;
 end
endmodule
