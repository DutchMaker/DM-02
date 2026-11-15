`timescale 1ns/1ps
module register_hardware_tb;
 reg osc=0,reset_n=1;initial #1 reset_n=0;
  always #(`DM02_OSC_PERIOD_NS/2) osc=~osc;
 wire [3:0] phase,state;wire active,ready;
 counted_clock clock(osc,reset_n,1'b1,1'b0,phase,active,ready,state);
 reg [3:0] loads=0,outs=0;reg drive=0,force_controls=0;reg [7:0] data=0;
 wire window=phase[2] || force_controls;
 wire [3:0] load_n=~(loads & {4{window}}),out_n=~(outs & {4{window}});
 tri [7:0] bus;wire [31:0] registers;
 assign bus=drive && phase[2] ? data : 8'bz;
 general_registers dut(phase[3],reset_n,load_n,out_n,bus,registers);
 reg [7:0] want[0:3];integer i,s,t,captures=0,transfers=0;
 task check;
 begin
   if(registers!=={want[0],want[1],want[2],want[3]})
     $fatal(1,"RG1 stored state got=%h want=%h",registers,{want[0],want[1],want[2],want[3]});
 end
 endtask
 task prepare;
 begin
   @(negedge phase[2]);#150;
   if(bus!==8'bz) $fatal(1,"RG1 idle bus release");
   loads=0;outs=0;drive=0;
 end
 endtask
 task load_byte(input integer target,input [7:0] value);
 begin
   prepare();loads=1<<target;drive=1;data=value;
   @(posedge phase[3]);want[target]=value;#100;check();captures=captures+1;
 end
 endtask
 initial begin
   for(i=0;i<4;i=i+1) want[i]=0;
   #1000;check();#1000;reset_n=1;#2000;check();
   for(i=0;i<256;i=i+1) begin
     for(t=0;t<4;t=t+1) load_byte(t,i^(t*61));
     for(s=0;s<4;s=s+1) begin
       load_byte(s,i^(s*37));
       for(t=0;t<4;t=t+1) begin
         prepare();outs=1<<s;loads=1<<t;
         @(posedge phase[2]);#200;
         if(bus!==want[s]) $fatal(1,"RG1 output byte source=%0d got=%h want=%h",s,bus,want[s]);
         @(posedge phase[3]);want[t]=want[s];#100;check();transfers=transfers+1;
       end
     end
   end
   // Assert reset with raw output/load commands still active, then clock while
   // reset is held. The board itself must inhibit the output and clear state.
   for(s=0;s<4;s=s+1) begin
     load_byte(s,8'ha5);prepare();outs=1<<s;loads=15;force_controls=1;
     #200;reset_n=0;#200;
     if(bus!==8'bz || registers!==0) $fatal(1,"RG1 reset inhibition source=%0d",s);
     #1000;outs=0;loads=0;force_controls=0;
     for(t=0;t<4;t=t+1) want[t]=0;
     #1000;reset_n=1;#2000;check();
   end
   $display("DONE RG1 captures=%0d transfers=%0d resets=4",captures,transfers);$finish;
 end
 initial begin #20000000;$fatal(1,"RG1 watchdog");end
endmodule
