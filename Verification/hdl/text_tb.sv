`timescale 1ns/1ps
module text_tb;
 parameter real PPM=0;
 localparam real RX_BIT=1.0e9/9600;
 reg osc=0,reset_n=1,strobe=0,rvalid=1;
 reg [7:0] waddr=0,wdata=0,raddr=3;
 wire [7:0] result;wire tx;
 text_dut dut(osc,reset_n,waddr,wdata,strobe,raddr,rvalid,result,tx);
 always #(125/(1+PPM/1e6)) osc=~osc;
 integer expected[0:1023],sent=0,received=0,busy_checks=0,epoch=0;
 reg monitor=0,no_frame=1;
 real first_start=-1,last_stop=-1;
 task write_byte(input [7:0] address,value);
   begin strobe=0;waddr=address;wdata=value;#700;strobe=1;#700;strobe=0;#700;end
 endtask
 task status(input [7:0] expected_status);
   begin raddr=3;rvalid=1;#700;if(result!==expected_status)
     $fatal(1,"TX1 status got=%h expected=%h",result,expected_status);end
 endtask
 task wait_ready;
   begin raddr=3;rvalid=1;#700;wait(result[0]===1);#700;end
 endtask
 task send(input [7:0] value);
   begin wait_ready;#((value*7919)%90000);expected[sent]=value;sent=sent+1;write_byte(0,value);end
 endtask
 always @(negedge tx)if(no_frame && reset_n)$fatal(1,"TX1 unexpected frame during initialization/idle");
 real last_edge=-1,spacing;integer edge_byte=-1,baud_edges=0;
 always @(tx)if(monitor && received<sent && expected[received]==85)begin
   if(edge_byte==received)begin
     spacing=$realtime-last_edge;
     if(spacing<104000/(1+PPM/1e6)-1 || spacing>104000/(1+PPM/1e6)+1)
       $fatal(1,"TX1 baud divider spacing=%0.3f",spacing);
     baud_edges=baud_edges+1;
   end
   last_edge=$realtime;edge_byte=received;
 end
 // Independent receiver sees only J2.2 and its own nominal 9600-baud clock.
 // It does not inspect baud, state, mailbox, request or acknowledgement nets.
 always @(negedge tx) if(monitor && reset_n) begin : receive_frame
   reg [7:0] value;integer i,token;reg valid;
   token=epoch;valid=1;
   if(first_start<0)first_start=$realtime;
   #(RX_BIT/2);if(tx!==0)valid=0;
   for(i=0;i<8;i=i+1)begin #(RX_BIT);value[i]=tx;end
   #(RX_BIT);if(tx!==1)valid=0;
   if(token==epoch && monitor)begin
     if(!valid)$fatal(1,"TX1 UART framing");
     if(received>=sent || value!==expected[received])
       $fatal(1,"TX1 serial mismatch index=%0d got=%h expected=%h sent=%0d",received,value,expected[received],sent);
     $display("RX %0d %02h",received,value);received=received+1;last_stop=$realtime;
   end
 end
 integer b;
 initial begin
   #1;reset_n=0;#2000;status(0);
   // Hold a transaction high across reset release: no new write edge exists.
   waddr=0;wdata=8'h33;strobe=1;#1000;reset_n=1;
   status(8'h80);#400000;
   if(tx!==1)$fatal(1,"TX1 reset-release phantom frame");
   strobe=0;status(8'h81);
   // A granted credit remains available without CPU activity.
   #2000000;status(8'h81);
   // Reserved writes/read qualifiers cannot consume the credit or assert status.
   write_byte(1,8'haa);write_byte(2,8'h55);write_byte(8'h10,8'hff);status(8'h81);
   for(b=0;b<256;b=b+1)begin
     raddr=b;#700;
     if(result!==(b==3?8'h81:8'h00))$fatal(1,"TX1 read decode alias address=%h",raddr);
   end
   raddr=3;rvalid=0;#700;if(result!==0)$fatal(1,"TX1 invalid read");rvalid=1;
   // Reset abort while an actual frame and queued byte exist, then reinitialize.
   no_frame=0;wait_ready;write_byte(0,8'h00);wait(tx===0);wait_ready;write_byte(0,8'h96);
   write_byte(0,8'h69);status(8'h82);#20000;
   epoch=epoch+1;reset_n=0;no_frame=1;#2000;status(0);
   if(tx!==1)$fatal(1,"TX1 reset failed to idle TX");
   #1000;reset_n=1;status(8'h80);#400000;status(8'h81);
   #2000000;if(tx!==1)$fatal(1,"TX1 reset retained queued byte");
   no_frame=0;monitor=1;
   for(b=0;b<256;b=b+1)begin
     send(b);
     if(b%17==1)begin
       status(8'h80);
       write_byte(0,~b);status(8'h82);
       write_byte(4,0);status(8'h82);
       write_byte(4,2);status(8'h80);busy_checks=busy_checks+1;
     end
   end
   // No more CPU events: the queued final byte must finish autonomously.
   wait(received==256);#(RX_BIT*2);status(8'h81);
   if(received!=sent || busy_checks!=15 || baud_edges!=9 || tx!==1)$fatal(1,"TX1 incomplete serial run");
   $display("PASS TX1 bytes=%0d busy_checks=%0d first_start_ns=%0.3f final_stop_ns=%0.3f",received,busy_checks,first_start,last_stop);
   $finish;
 end
 initial begin #500000000;$fatal(1,"TX1 timeout received=%0d sent=%0d status=%h",received,sent,result);end
endmodule
