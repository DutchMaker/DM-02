`timescale 1ns/1ps
module compact_counter_tb;
 parameter FULL=1;
 reg init_clk=0,reset_n=0,ph1=0,ph2=0,ph3=0,inc=0,dec=0,ll=1,lh=1;
 reg [7:0] value=0;reg host=0;
 wire [7:0] data_bus=host ? value : 8'bz;tri [7:0] source_bus;
 wire [15:0] address,sp;
 always #125 init_clk=~init_clk;
 stack_pointer stack(ph1,ph3,reset_n,inc,dec,ll,lh,1'b1,1'b1,data_bus,address,sp,init_clk,ph2,source_bus);
 integer i,checked=0;reg [15:0] expected;
 task cycle;
 begin
   @(posedge init_clk);#40;ph2=1;
   #750;ph3=1;
   #250;
   if(sp!==expected || address!==expected) $fatal(1,"CP counter mismatch row=%0d got=%h/%h want=%h",checked,sp,address,expected);
   checked=checked+1;ph2=0;ll=1;lh=1;
   #750;ph3=0;#50;
 end
 endtask
 initial begin
   #1;reset_n=1;#1;reset_n=0;
   #2000;@(negedge init_clk);#20;reset_n=1;#500;
   if(sp!==0) $fatal(1,"CP counter failed hardware zero preset");
   inc=1;
   for(i=1;i<=(FULL ? 65536 : 32);i=i+1) begin expected=i&65535;cycle();end
   inc=0;dec=1;
   for(i=1;i<=(FULL ? 65536 : 32);i=i+1) begin expected=(FULL ? -i : 32-i)&65535;cycle();end
   dec=0;host=1;
   for(i=0;i<256;i=i+1) begin
     value=i;ll=0;expected={sp[15:8],value};cycle();ll=1;
     value=255-i;lh=0;expected={value,sp[7:0]};cycle();lh=1;
   end
   host=0;
   if(sp!==16'h00ff) $fatal(1,"CP byte load final state");
   $display("DONE CP counter rows=%0d full=%0d",checked,FULL);$finish;
 end
 initial begin #500000000;$fatal(1,"CP counter watchdog");end
endmodule
