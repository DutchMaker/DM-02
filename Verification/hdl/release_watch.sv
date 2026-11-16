`timescale 1ns/1ps
// Independent drive-activity envelope. Same-valued competing drivers still fail.
// Zero earliest activation avoids borrowing the SRAM's 5 pF low-Z minimum.
module release_watch #(parameter real SRAM_RELEASE=10,WRITER_RELEASE=13)
 (input reset_n,read_n,write_n,ram_oe_n,ram_we_n,writer_oe_n,data_oe_n);
 wire ram_requested=!ram_oe_n && ram_we_n;
 wire writer_requested=!writer_oe_n;
 wire ram_active,writer_active;
 assign #(0,SRAM_RELEASE) ram_active=ram_requested;
 assign #(0,WRITER_RELEASE) writer_active=writer_requested;
 integer fd,overlaps=0;
 initial begin
   fd=$fopen("release-events.csv","w");
   if(!fd)$fatal(1,"RR1 event file");
   $fwrite(fd,"time_ns,reset_n,read_n,write_n,ram_oe_n,ram_we_n,writer_oe_n,data_oe_n\n");
 end
 always @(reset_n or read_n or write_n or ram_oe_n or ram_we_n or writer_oe_n or data_oe_n)
   $fwrite(fd,"%0.3f,%b,%b,%b,%b,%b,%b,%b\n",$realtime,reset_n,read_n,write_n,ram_oe_n,ram_we_n,writer_oe_n,data_oe_n);
 always @(ram_active or writer_active) begin
   if(ram_active===1'b1 && writer_active===1'b1)begin
     overlaps=overlaps+1;
     $fatal(1,"RR1 drive overlap (independent of data value)");
   end
 end
 final begin
   $display("RR1 activity overlaps=%0d SRAM_release=%0.3f writer_release=%0.3f",overlaps,SRAM_RELEASE,WRITER_RELEASE);
   $fclose(fd);
 end
endmodule
