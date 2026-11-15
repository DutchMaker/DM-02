module al1_rom #(parameter real TACC=100)(input [20:0] address,input ce_n,oe_n,output [15:0] q);
 reg [15:0] memory[0:2097151],value;integer fd,bytes_read,generation=0;
 initial begin
   fd=$fopen("alu.bin","rb");if(!fd) $fatal(1,"AL1 missing ROM");
   bytes_read=$fread(memory,fd);$fclose(fd);
   if(bytes_read!=4194304) $fatal(1,"AL1 ROM length");
 end
 assign q=value;
 task automatic resolve(input integer token,input [20:0] a,input ce,oe);
 begin #(TACC);if(generation==token) value=(ce || oe) ? 16'bz : memory[a];end
 endtask
 always @(address or ce_n or oe_n) begin
   generation=generation+1;value=16'bx;
   fork resolve(generation,address,ce_n,oe_n); join_none
 end
endmodule

module al1_377 #(parameter real TQ=57,TSU=18,TH=3,TEH=5,TPULSE=30)
 (input [7:0] d,input clk,enable_n,output [7:0] q,input reset_n);
 reg [7:0] stored;real ld=-10000,le=-10000,lc=-10000,lf=-10000;
 assign #(TQ) q=stored;
 always @(d) begin
   if(reset_n && !enable_n && $realtime-lc<TH) $fatal(1,"AL1 operand data hold %m");
   ld=$realtime;
 end
 always @(enable_n) begin
   if(reset_n && $realtime-lc<TEH) $fatal(1,"AL1 operand enable hold %m");
   le=$realtime;
 end
 always @(posedge clk) begin
   if(reset_n && $realtime-le<TSU) $fatal(1,"AL1 operand enable setup %m");
   if(reset_n && !enable_n && $realtime-ld<TSU) $fatal(1,"AL1 operand data setup %m");
   if(reset_n && $realtime-lf<TPULSE) $fatal(1,"AL1 operand low pulse %m");
   if(!enable_n) stored<=d;
   lc=$realtime;
 end
 always @(negedge clk) begin
   if(reset_n && $realtime-lc<TPULSE) $fatal(1,"AL1 operand high pulse %m");
   lf=$realtime;
 end
endmodule
