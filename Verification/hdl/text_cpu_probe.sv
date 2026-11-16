 parameter ABSENT=0;
 bridge_dut bridge(mar,mem_n,load_n[10],reset_n,ME1_RESET_n,
   physical_memory.io_address,physical_memory.io_data,physical_memory.io_strobe,
   card_data,{3'b110,ABSENT[0]},bridge_result,slot_waddr,slot_wdata,slot_raddr,
   slot_strobe,slot_read,slot_reset);
 reg text_osc=0;
 always #125 text_osc=~text_osc; // Independent local oscillator, continues at CPU HALT.
 wire serial_tx;wire [7:0] text_status;
 text_dut text_card(text_osc,slot_reset[0],slot_waddr[7:0],slot_wdata[7:0],slot_strobe[0],
                    slot_raddr[7:0],slot_read[0],text_status,serial_tx);
 assign card_data[7:0]=ABSENT ? 8'bz : text_status;
 reg [7:0] fixture=0;reg success=0;integer writes=0,reads=0,received=0,fd,rc;
 assign #40 card_data[15:8]=(slot_reset[1] && slot_read[1] && slot_raddr[15:8]==8'h10)?fixture:8'h00;
 assign card_data[31:16]=16'bz;
 always @(negedge slot_reset[1])fixture=0;
 always @(posedge slot_strobe[1])if(slot_reset[1] && slot_waddr[15:8]==8'h10)begin
   fixture=slot_wdata[15:8];
   if(fixture==8'h5a)success=1;
   if(fixture==8'hee && !ABSENT)$fatal(1,"TX1 CPU diagnostic error marker");
 end
 always @(posedge slot_strobe[0])if(slot_reset[0] && slot_waddr[7:0]==0)writes=writes+1;
 reg monitor=0;real last_data=-1e9,last_capture=-1e9,min_setup=1e9,min_hold=1e9;
 real halted_time=-1,final_stop=-1;
 always @(data_bus)begin
   if(monitor && last_capture>0 && $realtime-last_capture<min_hold)min_hold=$realtime-last_capture;
   last_data=$realtime;
 end
 always @(posedge AL1_PH3)if(monitor && AL1_RESET_n && !load_n[1] && !mem_n && mar[15:8]==8'hff)begin
   if($realtime-last_data<min_setup)min_setup=$realtime-last_data;
   if($realtime-last_data<35)$fatal(1,"TX1 CPU read setup reserve");
   last_capture=$realtime;reads=reads+1;
 end
 // Independent terminal decoder at nominal 9600 baud, only serial connector observed.
 always @(negedge serial_tx)if(monitor && !ABSENT)begin : receive
   reg [7:0] value,expected;integer i;
   #(1e9/9600/2);if(serial_tx!==0)$fatal(1,"TX1 CPU UART start");
   for(i=0;i<8;i=i+1)begin #(1e9/9600);value[i]=serial_tx;end
   #(1e9/9600);if(serial_tx!==1)$fatal(1,"TX1 CPU UART stop");
   rc=$fscanf(fd,"%h",expected);
   if(rc!=1 || value!==expected)$fatal(1,"TX1 CPU serial transcript got=%h expected=%h",value,expected);
   received=received+1;final_stop=$realtime;$display("CPU_RX %0d %h",received,value);
 end
 initial begin
   fd=$fopen("serial-expected.hex","r");if(!fd)$fatal(1,"TX1 CPU missing oracle");
   #2000;reset_request_n=1;run=1;monitor=1;
   @(posedge halted);halted_time=$realtime;#4000;
   if(active!==0 || phase[2]!==0 || phase[3]!==0)$fatal(1,"TX1 CPU halt");
   if(ABSENT)begin
     if(fixture!==8'hee || writes!=0 || success)$fatal(1,"TX1 CPU absence handling");
     $display("PASS TX1 CPU absent-device diagnostic");$finish;
   end
   if(!success || writes!=5)$fatal(1,"TX1 CPU incomplete writes");
   wait(received==5);#250000;
   if(final_stop<=halted_time)$fatal(1,"TX1 CPU final byte did not outlive HALT");
   if(min_hold<5)$fatal(1,"TX1 CPU read hold");
   rc=$fscanf(fd,"%h",fixture);if(rc==1)$fatal(1,"TX1 CPU unconsumed oracle");
   $display("PASS TX1 CPU received=%0d reads=%0d setup_ns=%0.3f hold_ns=%0.3f halted_ns=%0.3f final_stop_ns=%0.3f",
      received,reads,min_setup,min_hold,halted_time,final_stop);
   $finish;
 end
 initial begin #50000000;$fatal(1,"TX1 CPU timeout");end
