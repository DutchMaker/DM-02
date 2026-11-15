`timescale 1ns/1ps
module memory_hardware_tb;
 parameter QUICK=0;
 reg osc=0,reset_n=1;initial #1 reset_n=0;always #62.5 osc=~osc;
 wire [3:0] phase,state;wire active,ready;
 counted_clock clock(osc,reset_n,1'b1,1'b0,phase,active,ready,state);
 reg read_enable=0,write_enable=0,drive=0;reg [15:0] address=0;reg [7:0] data=0,io_input=0;
 tri [7:0] bus;wire [7:0] io_data,io_address;wire io_strobe;
 wire read_n=!(read_enable && phase[2]),write_n=!(write_enable && phase[2]);
 assign bus=drive && phase[2] ? data : 8'bz;
 memory_io dut(phase[0],phase[2],phase[3],reset_n,read_n,write_n,address,bus,io_input,io_data,io_address,io_strobe);
 integer i,reads=0,writes=0,protected_writes=0,io_seen=0,io_expected=0,before_writes;
 reg [7:0] want_io_data,want_io_address;real io_changed=-10000,io_captured=-10000;
 function [7:0] pattern(input [15:0] a);pattern=((a*37)^(a>>8)^'ha5)&255;endfunction
 always @(io_data or io_address) begin
   if(reset_n && $realtime-io_captured<40) $fatal(1,"ME1 IO connector hold");
   io_changed=$realtime;
 end
 always @(posedge io_strobe) if(reset_n) begin
   if($realtime-io_changed<40) $fatal(1,"ME1 IO connector setup");
   if(io_seen>=io_expected || io_data!==want_io_data || io_address!==want_io_address)
     $fatal(1,"ME1 IO output byte/address got=%h:%h want=%h:%h",io_address,io_data,want_io_address,want_io_data);
   io_seen=io_seen+1;io_captured=$realtime;
 end
 task prepare;
 begin
   @(negedge phase[2]);#150;
   if(bus!==8'bz) $fatal(1,"ME1 idle DATA release");
   if(io_seen!=io_expected) $fatal(1,"ME1 missing IO write");
   read_enable=0;write_enable=0;drive=0;
 end
 endtask
 task read_byte(input [15:0] a,input [7:0] want);
 begin
   prepare();address=a;read_enable=1;io_input=a[7:0]^'h5a;
   @(posedge phase[2]);#300;
   if(bus!==want) $fatal(1,"ME1 read address=%h got=%h want=%h",a,bus,want);
   @(posedge phase[3]);#100;reads=reads+1;
 end
 endtask
 task write_byte(input [15:0] a,input [7:0] value);
 begin
   prepare();address=a;write_enable=1;drive=1;data=value;before_writes=dut.U2.writes;
   if(a>=16'hff00) begin io_expected=io_expected+1;want_io_address=a[7:0];want_io_data=value;end
   @(posedge phase[3]);#100;
   if(a>=16'h4000 && a<16'hff00) begin
     if(dut.U2.writes!=before_writes+1) $fatal(1,"ME1 missing SRAM write");
     writes=writes+1;
   end else begin
     if(dut.U2.writes!=before_writes) $fatal(1,"ME1 protected ROM/IO wrote SRAM");
     if(a<16'h4000) protected_writes=protected_writes+1;
   end
 end
 endtask
 initial begin
   #2000;reset_n=1;#2000;
   for(i=0;i<65536;i=i+(QUICK ? 257 : 1)) read_byte(i,i>=65280 ? ((i&255)^'h5a) : pattern(i));
   for(i=16384;i<65280;i=i+(QUICK ? 257 : 1)) begin write_byte(i,pattern(i)^'h5a);read_byte(i,pattern(i)^'h5a);end
   for(i=0;i<16384;i=i+(QUICK ? 257 : 1)) begin write_byte(i,~pattern(i));read_byte(i,pattern(i));end
   for(i=0;i<256;i=i+1) begin write_byte('hff00+i,i^'ha5);read_byte('hff00+i,i^'h5a);end
   // Both commands asserted: blank read and write, including the IO request.
   prepare();address='h8000;read_enable=1;write_enable=1;before_writes=dut.U2.writes;
   @(posedge phase[2]);#300;if(bus!==8'bz) $fatal(1,"ME1 conflicting commands drive DATA");
   @(posedge phase[3]);#100;if(dut.U2.writes!=before_writes) $fatal(1,"ME1 conflicting commands write SRAM");
   write_byte('h4000,'h69);prepare();reset_n=0;#2000;reset_n=1;#2000;read_byte('h4000,'h69);
   prepare();read_enable=1;address=0;@(posedge phase[2]);#300;reset_n=0;#100;
   if(bus!==8'bz || io_strobe!==0) $fatal(1,"ME1 reset output inhibition");
   $display("DONE memory-io reads=%0d writes=%0d protected=%0d io=%0d",reads,writes,protected_writes,io_seen);$finish;
 end
 initial begin #250000000;$fatal(1,"ME1 watchdog");end
endmodule
