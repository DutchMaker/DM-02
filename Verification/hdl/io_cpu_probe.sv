 // BR1 attaches to actual R2 MAR, read/write controls and registered IO pins.
 parameter real ENDPOINT_NS=40,OSC_PERIOD_NS=250;
 parameter PRESENT_N=0;
 wire [7:0] bridge_result;
 wire [31:0] slot_waddr,slot_wdata,slot_raddr,card_data;
 wire [3:0] slot_strobe,slot_read,slot_reset;
 bridge_dut bridge(mar,mem_n,load_n[10],reset_n,ME1_RESET_n,
   physical_memory.io_address,physical_memory.io_data,physical_memory.io_strobe,
   card_data,PRESENT_N[3:0],bridge_result,slot_waddr,slot_wdata,slot_raddr,
   slot_strobe,slot_read,slot_reset);
 reg [7:0] fixture_value[0:3];
 integer observed=0,reads=0,cycles=0,fd,rc;
 reg [7:0] expected_byte;
 reg monitor=0;
 real last_data=-10000,min_read_setup=1.0e9;
 real last_capture=-10000,min_read_hold=1.0e9;
 real slot_change[0:3],slot_capture[0:3];
 genvar g;
 generate for(g=0;g<4;g=g+1) begin : fixture
   // Explicit behavioral qualification fixtures, not a text endpoint circuit.
   wire [7:0] reply=(slot_reset[g] && slot_read[g] &&
     slot_raddr[g*8+:8]==(g==0 ? 8'h03 : g*16)) ?
     (g==0 ? 8'h81 : fixture_value[g]) : 8'h00;
   assign #(ENDPOINT_NS) card_data[g*8+:8]=PRESENT_N[g] ? 8'bz : reply;
   initial begin fixture_value[g]=0;slot_change[g]=-10000;slot_capture[g]=-10000;end
   always @(negedge slot_reset[g]) fixture_value[g]=0;
   always @(slot_waddr[g*8+:8] or slot_wdata[g*8+:8]) begin
     if(monitor && slot_reset[g] && $realtime-slot_capture[g]<40)
       $fatal(1,"CPU bridge slot write hold slot=%0d",g+5);
     slot_change[g]=$realtime;
   end
   always @(posedge slot_strobe[g]) if(monitor && slot_reset[g]) begin
     if($realtime-slot_change[g]<40) $fatal(1,"CPU bridge slot write setup slot=%0d",g+5);
     slot_capture[g]=$realtime;
     if(g>0 && !PRESENT_N[g] && slot_waddr[g*8+:8]==g*16)
       fixture_value[g]=slot_wdata[g*8+:8];
     // Slot 5 instrumentation observes echoed bytes even in absent-card tests.
     // This observer never drives a return, modifies CPU state or supplies data.
     if(g==0 && slot_waddr[7:0]==0) begin
       rc=$fscanf(fd,"%h\n",expected_byte);
       if(rc!=1 || slot_wdata[7:0]!==expected_byte)
         $fatal(1,"CPU bridge echo mismatch event=%0d got=%h expected=%h",observed,slot_wdata[7:0],expected_byte);
       $display("ECHO %0d %h",observed,slot_wdata[7:0]);observed=observed+1;
     end
   end
 end endgenerate
 always @(data_bus) begin
   last_data=$realtime;
   if(monitor && last_capture>0 && $realtime-last_capture<min_read_hold)
     min_read_hold=$realtime-last_capture;
 end
 always @(posedge AL1_PH3) if(monitor && AL1_RESET_n && !load_n[1] && !mem_n && mar[15:8]==8'hff) begin
   if($realtime-last_data<min_read_setup) min_read_setup=$realtime-last_data;
   // 25 ns device setup plus the selected OC1 10 ns reserve, at this sample.
   if($realtime-last_data<35) $fatal(1,"CPU bridge sampled setup reserve below 10 ns");
   last_capture=$realtime;reads=reads+1;
   $display("READ_CAPTURE address=%h data=%h setup_ns=%0.3f",mar,data_bus,$realtime-last_data);
 end
 always @(posedge phase[3]) if(monitor) begin
   cycles=cycles+1;
   if(fetch1) begin #250;$display("FETCH pc=%h opcode=%h mar=%h",pc,opcode,mar);end
 end
 initial begin
   fd=$fopen("echo-expected.hex","r");if(!fd)$fatal(1,"CPU bridge expected file missing");
   #2000;reset_request_n=1;run=1;monitor=1;
   @(posedge halted);#4000;
   if(active!==0 || phase[2]!==0 || phase[3]!==0)$fatal(1,"CPU bridge halt did not stop clock");
   rc=$fscanf(fd,"%h",expected_byte);
   if(observed!=14 || reads!=12 || rc==1)$fatal(1,"CPU bridge incomplete diagnostic echoes=%0d reads=%0d pc=%h",observed,reads,pc);
   if(min_read_hold<5)$fatal(1,"CPU bridge sampled read hold below 5 ns");
   $display("PASS CPU bridge echoes=%0d reads=%0d cycles=%0d setup_ns=%0.3f hold_ns=%0.3f",observed,reads,cycles,min_read_setup,min_read_hold);
   // Asynchronous abort must remove read-valid and slot writes at settled reset.
   reset_request_n=0;run=0;#2000;
   if(slot_read!==0 || slot_strobe!==0 || bridge_result!==0)$fatal(1,"CPU bridge reset inactivity");
   $display("PASS CPU bridge reset");$finish;
 end
 initial begin #20000000;$fatal(1,"CPU bridge diagnostic timeout");end
