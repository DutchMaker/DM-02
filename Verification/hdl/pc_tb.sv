`timescale 1ns/1ps
module pc_tb;
 parameter COUNTED=0,QUICK=0,VECTORS=12288;
 reg osc=0,ideal=0,clock_reset_n=0,reset_n=0;
 always #62.5 osc=~osc;
 always #500 ideal=~ideal;
 wire [3:0] phase,state;
 wire active,ready;
 reg request=1,step=0;
 counted_clock source(osc,clock_reset_n,request,step,phase,active,ready,state);
 wire clock=COUNTED ? phase[3] : ideal;
 reg increment=0,load_l_n=1,load_h_n=1,out_l_n=1,out_h_n=1,address_n=1;
 reg drive=0;reg [7:0] data=0;
 tri [7:0] data_bus;tri [15:0] address_bus;
 wire [15:0] pc;
 assign data_bus=drive ? data : 8'bz;
 pc_candidate dut(clock,reset_n,increment,load_l_n,load_h_n,out_l_n,out_h_n,address_n,data_bus,address_bus,pc);
 integer increments=0,vectors=0,replayed=0;

 task blank;
 begin increment=0;load_l_n=1;load_h_n=1;out_l_n=1;out_h_n=1;address_n=1;drive=0;end
 endtask

 // Change controls well inside PH3 low, with explicit break-before-make.
 task cycle(input [7:0] value,input inc,ll,lh,ol,oh,addr,external_drive,
            input [15:0] before_pc,after_pc,input [7:0] expected_bus,input bus_valid);
 begin
   @(negedge clock);#50;blank();#40;
   data=value;drive=external_drive;increment=inc;load_l_n=!ll;load_h_n=!lh;
   out_l_n=!ol;out_h_n=!oh;address_n=!addr;
   #100;
   if(pc!==before_pc) $fatal(1,"PC before got=%h want=%h",pc,before_pc);
   if(bus_valid) begin
     if(data_bus!==expected_bus) $fatal(1,"PC data bus got=%h want=%h",data_bus,expected_bus);
   end else if(data_bus!==8'bz) $fatal(1,"PC data driver did not release");
   if(addr) begin
     if(address_bus!==before_pc) $fatal(1,"PC address bus got=%h want=%h",address_bus,before_pc);
   end else if(address_bus!==16'bz) $fatal(1,"PC address driver did not release");
   @(posedge clock);#150;
   if(pc!==after_pc) $fatal(1,"PC capture got=%h want=%h",pc,after_pc);
 end
 endtask

 task seed(input [15:0] value);
 reg [15:0] old;
 begin
   old=pc;
   cycle(value[7:0],0,1,0,0,0,0,1,old,{old[15:8],value[7:0]},value[7:0],1);
   old=pc;
   cycle(value[15:8],0,0,1,0,0,0,1,old,value,value[15:8],1);
 end
 endtask

 integer i,fd,rc,ctl;
 reg [15:0] before_pc,after_pc;
 reg [7:0] value,expected_bus;
 integer inc,ll,lh,ol,oh,addr,valid,start;
 initial begin
   #1000;clock_reset_n=1;
   @(negedge clock);#100;reset_n=1;
   cycle(0,0,0,0,0,0,0,0,0,0,0,0);
   for(i=0;i<(QUICK ? 32 : 65536);i=i+1) begin
     cycle(0,1,0,0,0,0,1,0,i[15:0],(i+1)&16'hffff,0,0);
     increments=increments+1;
   end
   fd=$fopen("vectors.txt","r");if(!fd) $fatal(1,"Missing PC vectors");
   while(!$feof(fd)) begin
     rc=$fscanf(fd,"%h %h %h %h\n",before_pc,value,ctl,after_pc);
     if(rc!=4) $fatal(1,"Malformed PC vector");
     seed(before_pc);
     cycle(value,ctl[0],ctl[1],ctl[2],0,0,0,1,before_pc,after_pc,value,1);
     vectors=vectors+1;
   end
   $fclose(fd);
   // Independently selected byte and address outputs, plus opposing-driver probe.
   seed(16'ha55a);
   cycle(0,0,0,0,1,0,0,0,16'ha55a,16'ha55a,8'h5a,1);
   cycle(0,0,0,0,0,1,1,0,16'ha55a,16'ha55a,8'ha5,1);
   cycle(0,0,0,0,0,0,1,0,16'ha55a,16'ha55a,0,0);
   @(negedge clock);#50;blank();#40;out_l_n=0;out_h_n=0;#100;
   if(data_bus!==8'hxx) $fatal(1,"Opposing PC drivers were not resolved to X");
   // Reset must override loads/increment and inhibit every output even with OEs low.
   reset_n=0;increment=1;load_l_n=0;load_h_n=0;address_n=0;
   #1000;
   if(pc!==0 || data_bus!==8'bz || address_bus!==16'bz) $fatal(1,"PC reset priority/inhibition");
   @(negedge clock);#50;blank();#50;reset_n=1;
   cycle(0,0,0,0,0,0,0,0,0,0,0,0);
   if(COUNTED) begin
     request=0;#3000;
     if(active!==0 || phase[3]!==0 || pc!==0) $fatal(1,"PC clock stop did not hold");
     increment=1;#3000;
     if(pc!==0) $fatal(1,"PC changed while clock stopped");
     step=1;#4000;
     if(pc!==1 || active!==0) $fatal(1,"PC first step lost/repeated");
     #4000;
     if(pc!==1) $fatal(1,"PC repeated held STEP");
     step=0;#3000;step=1;#4000;
     if(pc!==2 || active!==0) $fatal(1,"PC second step lost/repeated");
     step=0;increment=0;request=1;#3000;
   end
   fd=$fopen("replay.txt","r");if(!fd) $fatal(1,"Missing PC replay");
   while(!$feof(fd)) begin
     rc=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h\n",
       before_pc,value,inc,ll,lh,ol,oh,addr,after_pc,expected_bus,valid,start);
     if(rc==-1) begin end
     else begin
       if(rc!=12) $fatal(1,"Malformed PC replay");
       if(start) seed(before_pc);
       cycle(value,inc,ll,lh,ol,oh,addr,valid && !ol && !oh,before_pc,after_pc,expected_bus,valid);
       replayed=replayed+1;
     end
   end
   $fclose(fd);
   if(increments!=(QUICK ? 32 : 65536) || vectors!=VECTORS) $fatal(1,"Incomplete PC coverage");
   $display("DONE pc-candidate increments=%0d vectors=%0d replay=%0d counted=%0d",increments,vectors,replayed,COUNTED);
   $finish;
 end
 initial begin #500000000; $fatal(1,"PC watchdog");end
endmodule
