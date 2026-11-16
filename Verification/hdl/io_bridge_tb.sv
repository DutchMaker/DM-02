`timescale 1ns/1ps
module bridge_tb;
 reg [15:0] address=0;
 reg mem_n=0,write_n=1,reset_n=0,strobe=0;
 // Separate memory reset branch; sample skew exercises the native boundary.
 wire memory_reset_n;
 assign #70 memory_reset_n=reset_n;
 reg [7:0] waddr=8'hca,wdata=8'h35;
 reg [31:0] card_data=32'h96695aa5;
 reg [3:0] present_n=4'b1111;
 wire [7:0] result;
 wire [31:0] slot_waddr,slot_wdata,slot_raddr;
 wire [3:0] slot_strobe,slot_read,slot_reset;
 integer writes[0:3];integer a,p,b,s;integer cases=0;
 bridge_dut dut(address,mem_n,write_n,reset_n,memory_reset_n,waddr,wdata,strobe,card_data,present_n,
  result,slot_waddr,slot_wdata,slot_raddr,slot_strobe,slot_read,slot_reset);
 genvar g;
 generate for(g=0;g<4;g=g+1) begin
  always @(posedge slot_strobe[g]) if(slot_reset[g]===1'b1) begin
   writes[g]=writes[g]+1;
   if(slot_waddr[g*8+:8]!==waddr || slot_wdata[g*8+:8]!==wdata)
    $fatal(1,"Write address/data mismatch on slot %0d",g+5);
  end
 end endgenerate
 function [7:0] expected;
  input [15:0] addr;
  begin
   expected=0;
   if(reset_n && memory_reset_n && !mem_n && write_n) case(addr)
    16'hff03:if(!present_n[0])expected=card_data[7:0];
    16'hff10:if(!present_n[1])expected=card_data[15:8];
    16'hff20:if(!present_n[2])expected=card_data[23:16];
    16'hff30:if(!present_n[3])expected=card_data[31:24];
   endcase
  end
 endfunction
 task check;
  begin
   #1500;
   if(result!==expected(address))$fatal(1,"Read mismatch addr=%h got=%h expected=%h",address,result,expected(address));
   for(integer k=0;k<4;k=k+1) begin
    if(slot_raddr[k*8+:8]!==address[7:0])$fatal(1,"Read forwarding mismatch");
    if(slot_read[k]!==((address[15:8]==8'hff)&&!mem_n&&write_n&&memory_reset_n))$fatal(1,"Read qualifier mismatch");
   end
   cases=cases+1;
  end
 endtask
 task zero_counts;
  begin for(integer k=0;k<4;k=k+1)writes[k]=0;end
 endtask
 task count_is(input integer n);
  begin for(integer k=0;k<4;k=k+1)if(writes[k]!=n)$fatal(1,"Write count slot%0d got%0d expected%0d",k+5,writes[k],n);end
 endtask
 initial begin
  zero_counts();#2000;reset_n=1;present_n=0;
  // Entire memory space, including non-IO high-byte aliases.
  for(a=0;a<65536;a=a+1)begin address=a;check();end
  // Every presence mask and every low-byte address, with opposing returns.
  for(p=0;p<16;p=p+1)begin
   reset_n=0;#2000;present_n=p;#2000;reset_n=1;
   for(a=0;a<256;a=a+1)begin address=16'hff00+a;check();end
  end
  // Walking data bits exercise every private-return wire and mux channel.
  reset_n=0;#2000;present_n=0;#2000;reset_n=1;
  for(b=0;b<32;b=b+1)begin
   card_data=32'b1<<b;
   address=16'hff03;check();address=16'hff10;check();address=16'hff20;check();address=16'hff30;check();
  end
  for(p=0;p<4;p=p+1)begin
   mem_n=p[0];write_n=p[1];address=16'hff03;check();
  end
  mem_n=0;write_n=1;card_data=32'h96695aa5;
  // Empty connectors float; resistor defaults must still yield zero.
  reset_n=0;#2000;present_n=4'bzzzz;card_data=32'bz;#2000;reset_n=1;
  address=16'hff03;#2000;if(result!==0)$fatal(1,"Empty slot default");
  reset_n=0;#2000;present_n=0;card_data=32'h96695aa5;#2000;
  $dumpfile("reset-write.vcd");$dumpvars(0,bridge_tb);
  // Reset release while raw strobe is high must not replay a previous byte.
  strobe=1;#2000;zero_counts();reset_n=1;#2000;count_is(0);
  if(slot_strobe!==0)$fatal(1,"Reset release created write event");
  strobe=0;#2000;waddr=8'h04;wdata=8'h02;#2000;
  strobe=1;#2000;count_is(1);
  // Assert reset during a pending strobe, then release without a new edge.
  reset_n=0;#2000;zero_counts();reset_n=1;#2000;count_is(0);
  if(slot_strobe!==0)$fatal(1,"Reset abort/release replayed write");
  strobe=0;#2000;
  // Writes and reads carry independent addresses; live address transitions
  // must never generate a write event or use the registered write address.
  for(a=0;a<256;a=a+1)begin
   waddr=a;wdata=a^8'ha5;address=(a[0]?16'hff03:16'hff10);check();
   strobe=1;#1000;strobe=0;#1000;
  end
  count_is(256);
  $display("PASS bridge read_cases=%0d write_cases=256 reset-release/abort/defaults",cases);
  $finish;
 end
 initial begin #300000000;$fatal(1,"Bridge timeout");end
endmodule
