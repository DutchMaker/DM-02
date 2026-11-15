`timescale 1ns/1ps
module flash_array_tb;
 reg [20:0] address=0;wire [15:0] result;
 flash_array dut(address,result);
 reg [7:0] expected[0:4194303];integer fd,rc,i,bank;
 task check(input [20:0] a);
 begin
   address=a;#120;
   if(result!=={expected[2*a+1],expected[2*a]}) $fatal(1,"FR1 read a=%h got=%h",a,result);
 end
 endtask
 initial begin
   fd=$fopen("alu-original.bin","rb");if(!fd) $fatal(1,"FR1 missing oracle image");
   rc=$fread(expected,fd);$fclose(fd);if(rc!=4194304) $fatal(1,"FR1 oracle length");
   #90000;if(!$isunknown(result)) $fatal(1,"FR1 startup qualification bypassed");
   #11000;
   for(bank=0;bank<4;bank=bank+1) begin
     for(i=0;i<8192;i=i+1) check((bank<<19)|((i*257)&'h7ffff));
     check(bank<<19);check((bank<<19)|'h7ffff);
   end
   $display("DONE FR1 checks=32776");$finish;
 end
endmodule
