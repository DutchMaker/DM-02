`timescale 1ns/1ps
module alu_hardware_tb;
 parameter QUICK=0,STARTUP_WAIT_NS=0;
 reg osc=0,reset_n=1;initial #1 reset_n=0;
  always #(`DM02_OSC_PERIOD_NS/2) osc=~osc;
 wire [3:0] phase,state;wire active,ready;
 counted_clock clock(osc,reset_n,1'b1,1'b0,phase,active,ready,state);
 reg al=0,bl=0,fl=0,ao=0,bo=0,fo=0,drive=0;
 reg [3:0] commands=0;reg [4:0] operation=0;reg [7:0] data=0;
 wire window=phase[2] && reset_n;
 tri [7:0] bus;wire [7:0] a;wire [3:0] flags;wire [20:0] address;wire [15:0] result;
 assign bus=drive && window ? data : 8'bz;
 timed_alu dut(phase[1],phase[3],reset_n,!(al&&window),!(bl&&window),!(fl&&window),
   !(ao&&window),!(bo&&window),!(fo&&window),commands[0]&&window,commands[1]&&window,
   commands[2]&&window,commands[3]&&window,operation,bus,a,flags,address,result);
 reg [36:0] vectors[0:8191],vector;reg [3:0] saved,want_flags;reg [15:0] want;
 integer i,j,checks=0,roundtrips=0,command_checks=0;
 task prepare;
 begin
   @(negedge phase[2]);#150;
   if(bus!==8'bz) $fatal(1,"AL1 idle bus release");
   al=0;bl=0;fl=0;ao=0;bo=0;fo=0;drive=0;commands=0;
 end
 endtask
 task capture;
 begin @(posedge phase[3]);#100;end
 endtask
 initial begin
    $readmemh("vectors.hex",vectors);
    #(STARTUP_WAIT_NS);
   #2000;reset_n=1;#2000;
   if(a!==0 || flags!==0) $fatal(1,"AL1 startup reset state");
   for(i=0;i<(QUICK ? 256 : 8192);i=i+1) begin
     vector=vectors[QUICK ? i*32 : i];want=vector[15:0];saved=flags;
     prepare();al=1;drive=1;data=vector[31:24];capture();
     if(a!==vector[31:24] || flags!==saved) $fatal(1,"AL1 A capture/flag hold");
     prepare();bl=1;drive=1;data=vector[23:16];operation=vector[36:32];capture();
     if(address!==vector[36:16] || flags!==saved) $fatal(1,"AL1 operand/operation capture");
     prepare();bo=1;al=1;
     // Opcode/operand connector changes after capture must not change the result.
     operation=~operation;data=~data;
     @(posedge phase[2]);#200;
     if(bus!==want[7:0] || result[11:0]!==want[11:0]) $fatal(1,"AL1 ROM result vector=%0d got=%h want=%h",i,result,want);
     capture();
     if(a!==want[7:0] || flags!==want[11:8]) $fatal(1,"AL1 simultaneous A/flags vector=%0d",i);
     prepare();fo=1;@(posedge phase[2]);#200;
     if(bus!=={4'b0,want[11:8]}) $fatal(1,"AL1 packed F output");
     capture();if(flags!==want[11:8]) $fatal(1,"AL1 feedback changed stored flags");
     checks=checks+1;
   end
   for(i=0;i<256;i=i+1) begin
     prepare();fl=1;drive=1;data=i;capture();
     if(flags!==i[3:0]) $fatal(1,"AL1 F load/masking");
     prepare();fo=1;@(posedge phase[2]);#200;
     if(bus!=={4'b0,i[3:0]}) $fatal(1,"AL1 F roundtrip");
     capture();roundtrips=roundtrips+1;
   end
   for(i=0;i<16;i=i+1) for(j=0;j<4;j=j+1) begin
     prepare();fl=1;drive=1;data=i;capture();
     prepare();commands=1<<j;want_flags=i;
     case(j) 0:want_flags[0]=1;1:want_flags[2]=1;2:want_flags[0]=0;3:want_flags[2]=0;endcase
     @(posedge phase[2]);#200;
     if(flags!==i[3:0]) $fatal(1,"AL1 command changed flags before PH3");
     capture();if(flags!==want_flags) $fatal(1,"AL1 synchronous command");
     command_checks=command_checks+1;
   end
   prepare();ao=1;@(posedge phase[2]);#200;
   if(bus!==a) $fatal(1,"AL1 A output");
   reset_n=0;#200;
   if(bus!==8'bz || flags!==0 || a!==0) $fatal(1,"AL1 reset inhibition");
   $display("DONE AL1 vectors=%0d F=%0d commands=%0d",checks,roundtrips,command_checks);$finish;
 end
 initial begin #50000000;$fatal(1,"AL1 watchdog");end
endmodule
