`timescale 1ns/1ps
module controller_tb;
 parameter PATTERN=1,COUNTED=1,QUICK=0;
 reg osc=0,clock_reset_n=0,reset_n=0;
 wire [3:0] counted_phase,state;wire active,ready;
 generate if(COUNTED) begin : counted
   always #62.5 osc=~osc;
   counted_clock source(osc,clock_reset_n,1'b1,1'b0,counted_phase,active,ready,state);
 end endgenerate
 reg ideal2=0,ideal3=0;
 initial begin #2000;forever begin ideal2=1;#500;ideal2=0;#500;end end
 initial begin #2375;forever begin ideal3=1;#500;ideal3=0;#500;end end
 wire [3:0] phase=COUNTED ? counted_phase : {ideal3,ideal2,~ideal3,~ideal2};
 reg [15:0] address=0;wire [15:0] word;
 wire [14:1] out_n,load_n;wire [12:1] functions;
 wire [4:0] alu_op;wire alu_enable,pc_address_n,valid;
 control_word dut(phase[1],phase[2],reset_n,address,word,out_n,load_n,functions,alu_op,alu_enable,pc_address_n,valid);
 reg seed_mode=0,seed_ll=0,seed_lh=0,drive=0;
 reg [7:0] data=0;tri [7:0] data_bus;tri [15:0] address_bus;wire [15:0] pc;
 assign data_bus=drive ? data : 8'bz;
 pc_candidate counter(phase[3],PATTERN ? 1'b0 : reset_n,seed_mode ? 1'b0 : functions[5],
   seed_mode ? !seed_ll : load_n[12],seed_mode ? !seed_lh : load_n[11],
   seed_mode ? 1'b1 : out_n[12],seed_mode ? 1'b1 : out_n[11],
   seed_mode ? 1'b1 : pc_address_n,data_bus,address_bus,pc);

 task inactive;
 begin
   if(out_n!==14'h3fff || load_n!==14'h3fff || functions!==0 || alu_enable!==0 || pc_address_n!==1)
     $fatal(1,"CW outputs not inhibited out=%h load=%h functions=%h",out_n,load_n,functions);
 end
 endtask

 task decoded(input [15:0] w);
 reg [14:1] expected_out,expected_load;reg [12:1] expected_functions;
 integer o,l,a,b;
 begin
   expected_out=14'h3fff;expected_load=14'h3fff;expected_functions=0;
   o=(w>>11)&15;l=(w>>7)&15;a=(w>>11)&15;b=(w>>1)&15;
   if(w[15]) begin
     if(o>0 && o<15) expected_out[o]=0;
     if(l>0 && l<15) expected_load[l]=0;
     if(!w[6] && b>0 && b<13) expected_functions[b]=1;
   end else begin
     if(a>0 && a<13) expected_functions[a]=1;
     if(b>0 && b<13) expected_functions[b]=1;
   end
   if(word!==w) $fatal(1,"CW word got=%h want=%h address=%h",word,w,address);
   if(out_n!==expected_out || load_n!==expected_load || functions!==expected_functions)
     $fatal(1,"CW decode word=%h out=%h/%h load=%h/%h functions=%h/%h",w,out_n,expected_out,load_n,expected_load,functions,expected_functions);
   if(alu_op!==w[5:1] || alu_enable!==(w[15] && w[6]) || pc_address_n!==!expected_functions[6])
     $fatal(1,"CW ALU/function mapping");
 end
 endtask

 task cycle(input [15:0] addr,w,before_pc,after_pc,input [7:0] bus_value,input bus_valid);
 reg pc_output;
 begin
   @(negedge phase[2]);#140;
   inactive();address=addr;seed_mode=0;seed_ll=0;seed_lh=0;
   pc_output=w[15] && (((w>>11)&15)==11 || ((w>>11)&15)==12);
   drive=!PATTERN && bus_valid && !pc_output;data=bus_value;
   @(posedge phase[1]);#80;
   if(word!==w) $fatal(1,"CW capture word got=%h want=%h",word,w);
   // Change opcode, t-state and flags while the captured word must stay fixed.
   address=addr^16'hffff;
   @(posedge phase[2]);#180;
   decoded(w);
   if(!PATTERN) begin
     if(pc!==before_pc) $fatal(1,"CW PC before got=%h want=%h",pc,before_pc);
     if(bus_valid) begin
       if(data_bus!==bus_value) $fatal(1,"CW PC data bus got=%h want=%h",data_bus,bus_value);
     end else if(data_bus!==8'bz) $fatal(1,"CW PC data bus release");
     if(functions[6]) begin
       if(address_bus!==before_pc) $fatal(1,"CW PC address bus got=%h want=%h",address_bus,before_pc);
     end else if(address_bus!==16'bz) $fatal(1,"CW PC address bus release");
   end
   @(posedge phase[3]);#95;
   if(word!==w) $fatal(1,"CW address/flag change leaked through word latch");
   if(!PATTERN && pc!==after_pc) $fatal(1,"CW PC capture got=%h want=%h",pc,after_pc);
 end
 endtask

 task seed_byte(input [7:0] value,input high_byte);
 begin
   @(negedge phase[3]);#50;
   seed_mode=1;seed_ll=0;seed_lh=0;drive=0;#40;
   data=value;drive=1;seed_ll=!high_byte;seed_lh=high_byte;
   @(posedge phase[3]);#95;
 end
 endtask
 task seed(input [15:0] value);
 begin seed_byte(value[7:0],0);seed_byte(value[15:8],1);if(pc!==value) $fatal(1,"CW fixture seed");end
 endtask

 integer i,fd,rc,checked=0,replayed=0,start,bus_valid;
 reg [15:0] addr,w,before_pc,after_pc;reg [7:0] bus_value;
 integer driver_count,j;reg monitor=0;
 always @(out_n) begin
   driver_count=0;
   for(j=1;j<=14;j=j+1) if(out_n[j]===0) driver_count=driver_count+1;
   if(monitor && driver_count>1) $fatal(1,"CW overlapping output selectors");
 end
 initial begin
   #1000;clock_reset_n=1;
   @(posedge phase[3]);#100;inactive();reset_n=1;
   if(PATTERN) begin
     for(i=0;i<(QUICK ? 256 : 65536);i=i+1) begin
       addr=(i*257)&16'hffff;w=addr^16'ha5c3;
       cycle(addr,w,0,0,0,0);checked=checked+1;monitor=1;
       if((checked%8192)==0) $display("PROGRESS control-word words=%0d",checked);
     end
   end else begin
     fd=$fopen("replay.txt","r");if(!fd) $fatal(1,"Missing controller replay");
     while(!$feof(fd)) begin
       rc=$fscanf(fd,"%h %h %h %h %h %h %h\n",addr,w,before_pc,after_pc,bus_value,bus_valid,start);
       if(rc!=-1) begin
         if(rc!=7) $fatal(1,"Malformed controller replay");
         if(start) seed(before_pc);
         cycle(addr,w,before_pc,after_pc,bus_value,bus_valid);replayed=replayed+1;monitor=1;
       end
     end
     $fclose(fd);
     if(replayed==0) $fatal(1,"Empty controller replay");
   end
   // Reset during an enabled interval must clear validity and inhibit all controls.
   @(posedge phase[2]);#180;reset_n=0;#200;inactive();
   if(valid!==0) $fatal(1,"CW reset validity");
   #1000;@(negedge phase[1]);#100;reset_n=1;#100;inactive();
   if(valid!==0) $fatal(1,"CW enabled before first word capture");
   $display("DONE control-word words=%0d replay=%0d counted=%0d",checked,replayed,COUNTED);$finish;
 end
 initial begin #300000000;$fatal(1,"CW watchdog");end
endmodule
