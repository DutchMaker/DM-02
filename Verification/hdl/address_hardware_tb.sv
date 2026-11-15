`timescale 1ns/1ps
module address_hardware_tb;
 parameter QUICK=0;
 reg osc=0,reset_n=1;initial #1 reset_n=0;always #62.5 osc=~osc;
 wire [3:0] phase,state;wire active,ready;
 counted_clock clock(osc,reset_n,1'b1,1'b0,phase,active,ready,state);
 reg si=0,sd=0,mi=0,fetch0=0,pt=0,st=0,drive=0,force_controls=0;
 reg [1:0] sl=0,so=0,ml=0,mo=0;reg [7:0] data=0;reg [15:0] pc=0;
 wire window=phase[2] || force_controls;
 tri [7:0] bus;wire [15:0] sp,sp_address,mar;
 assign bus=drive && phase[2] ? data : 8'bz;
 stack_pointer stack(phase[1],phase[3],reset_n,si&&window,sd&&window,!(sl[0]&&window),!(sl[1]&&window),
                     !(so[0]&&window),!(so[1]&&window),bus,sp_address,sp);
 memory_address address(phase[1],phase[3],reset_n,mi&&window,fetch0&&window,pt&&window,st&&window,
                        !(ml[0]&&window),!(ml[1]&&window),!(mo[0]&&window),!(mo[1]&&window),pc,sp_address,bus,mar);
 reg [15:0] want_sp=0,want_mar=0,before_sp,before_mar,saved;
 integer i,j,k,counts=0,transfers=0,vectors=0;
 task check;
 begin
   if(sp!==want_sp || mar!==want_mar)
     $fatal(1,"address state sp=%h/%h mar=%h/%h",sp,want_sp,mar,want_mar);
 end
 endtask
 task prepare;
 begin
   @(negedge phase[2]);#150;
   if(bus!==8'bz) $fatal(1,"address idle DATA release");
   check();si=0;sd=0;mi=0;fetch0=0;pt=0;st=0;sl=0;so=0;ml=0;mo=0;drive=0;
 end
 endtask
 task capture;
 begin @(posedge phase[3]);#100;check();end
 endtask
 task set_sp(input [15:0] value);
 begin
   prepare();drive=1;sl=1;data=value[7:0];want_sp[7:0]=data;capture();
   prepare();drive=1;sl=2;data=value[15:8];want_sp[15:8]=data;capture();
 end
 endtask
 task set_mar(input [15:0] value);
 begin
   prepare();drive=1;ml=1;data=value[7:0];want_mar[7:0]=data;capture();
   prepare();drive=1;ml=2;data=value[15:8];want_mar[15:8]=data;capture();
 end
 endtask
 initial begin
   #1000;check();#1000;reset_n=1;#2000;check();
   for(i=0;i<(QUICK ? 64 : 65536);i=i+1) begin
     prepare();si=1;want_sp=want_sp+1'b1;capture();counts=counts+1;
   end
   for(i=0;i<(QUICK ? 64 : 65536);i=i+1) begin
     prepare();sd=1;want_sp=want_sp-1'b1;capture();counts=counts+1;
   end
   for(i=0;i<(QUICK ? 64 : 65536);i=i+1) begin
     prepare();mi=1;want_mar=want_mar+1'b1;capture();counts=counts+1;
   end
   // Every address, including PC changes at the same PH3 edge as MAR capture.
   for(i=0;i<(QUICK ? 256 : 65536);i=i+1) begin
     prepare();pc=QUICK ? i*257 : i;want_mar=pc;
     if(i&1) pt=1;else fetch0=1;
     @(posedge phase[2]);#200;
     if(mar!==want_mar) $fatal(1,"MAR early PC address transfer");
     @(posedge phase[3]);pc=pc+1'b1;#100;check();transfers=transfers+1;
   end
   for(i=0;i<16;i=i+1) for(j=0;j<16;j=j+1) begin
     set_sp((i<<12)|(j<<4)|15);
     prepare();st=1;si=1;want_mar=want_sp;want_sp=want_sp+1'b1;
     @(posedge phase[2]);#200;
     if(mar!==want_mar) $fatal(1,"MAR early SP address transfer");
     capture();transfers=transfers+1;
   end
   // Byte load wins over arithmetic in that byte, preserving carry/borrow in
   // the other byte. Conflicting increment/decrement cancel arithmetically.
   for(i=0;i<4;i=i+1) for(j=0;j<16;j=j+1) begin
     case(i) 0:saved='h00ff;1:saved='hff00;2:saved='hffff;3:saved='h1234;endcase
     set_sp(saved);set_mar(saved);
     prepare();drive=1;data=j*17;si=j&1;sd=(j>>1)&1;sl=j>>2;
     want_sp=saved+si-sd;
     if(sl[0]) want_sp[7:0]=data;if(sl[1]) want_sp[15:8]=data;
     capture();vectors=vectors+1;
     prepare();drive=1;data=255-j*17;mi=j&1;ml=j>>2;
     want_mar=saved+mi;
     if(ml[0]) want_mar[7:0]=data;if(ml[1]) want_mar[15:8]=data;
     capture();vectors=vectors+1;
   end
   set_sp('h5aa5);set_mar('hc33c);
   for(i=0;i<4;i=i+1) begin
     prepare();case(i) 0:so=1;1:so=2;2:mo=1;3:mo=2;endcase
     @(posedge phase[2]);#200;
     if(bus!==(i==0 ? 8'ha5 : i==1 ? 8'h5a : i==2 ? 8'h3c : 8'hc3)) $fatal(1,"address byte output");
     capture();
   end
   // Raw output controls stay asserted across reset.
   prepare();so=1;force_controls=1;#200;reset_n=0;want_sp=0;want_mar=0;#200;check();
   if(bus!==8'bz) $fatal(1,"stack reset DATA inhibition");
   so=0;mo=1;#200;if(bus!==8'bz) $fatal(1,"MAR reset DATA inhibition");
   $display("DONE address-path counts=%0d transfers=%0d vectors=%0d",counts,transfers,vectors);$finish;
 end
 initial begin #400000000;$fatal(1,"address watchdog");end
endmodule
