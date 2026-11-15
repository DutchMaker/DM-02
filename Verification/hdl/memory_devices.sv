module me_rom #(parameter real TACC=70)(input [15:0] address,input ce_n,oe_n,output [7:0] q);
 reg [7:0] memory[0:65535],value;integer version=0,generation=0;
 initial $readmemh("program.hex",memory);
 assign q=value;
 task automatic resolve(input integer token,input [15:0] a,input ce,oe);
 begin #(TACC);if(generation==token) value=(ce || oe) ? 8'bz : memory[a];end
 endtask
 always @(address or ce_n or oe_n or version) begin
   generation=generation+1;value=8'bx;
   fork resolve(generation,address,ce_n,oe_n);join_none
 end
endmodule

module me_sram #(parameter real TACC=55,TDIS=20,TWC=55,TAW=50,TWP=45,TDW=25)
 (input [16:0] address,input ce_n,ce2,oe_n,we_n,inout [7:0] dq,input reset_n);
 reg [7:0] memory[0:131071],value;integer version=0,generation=0,writes=0;
 reg writing=0;reg [16:0] write_address;
 real last_address=-10000,last_data=-10000,write_start=-10000,previous_start=-10000,selected_since=-10000;
 initial $readmemh("program.hex",memory,0,65535);
 wire selected=!ce_n && ce2;
 assign dq=value;
 task automatic resolve(input integer token,input [16:0] a,input reading);
 begin
   #(reading ? TACC : TDIS);
   if(generation==token) value=reading ? memory[a] : 8'bz;
 end
 endtask
 always @(address or ce_n or ce2 or oe_n or we_n or version) begin
   generation=generation+1;
   if(selected && !oe_n && we_n) value=8'bx;
   fork resolve(generation,address,selected && !oe_n && we_n);join_none
 end
 always @(address) begin
   if(reset_n && writing) $fatal(1,"ME1 SRAM address changed during write");
   last_address=$realtime;
 end
 always @(dq) last_data=$realtime;
 always @(posedge selected) selected_since=$realtime;
 always @(negedge we_n) if(selected && reset_n) begin
   if($realtime-previous_start<TWC) $fatal(1,"ME1 SRAM write cycle");
   if(!oe_n) $fatal(1,"ME1 SRAM OE active during write");
   writing=1;write_start=$realtime;previous_start=$realtime;write_address=address;
 end
 always @(posedge we_n or negedge selected) if(writing) begin
   if(reset_n) begin
     if($realtime-write_start<TWP) $fatal(1,"ME1 SRAM write pulse");
     if($realtime-last_address<TAW || $realtime-selected_since<TAW) $fatal(1,"ME1 SRAM address/select setup");
     if($realtime-last_data<TDW) $fatal(1,"ME1 SRAM data setup");
     if($isunknown(dq)) $fatal(1,"ME1 SRAM invalid write data");
     memory[write_address]=dq;version=version+1;writes=writes+1;
   end else $display("ME1 RESET_ABORT: interrupted SRAM write is unqualified");
   writing=0;
 end
endmodule
