 // TB1 observes the native SRAM write counter and CPU address/fetch state.
 // The only memory initialization performed by the harness is poisoned SRAM
 // and the physical ROM image; payload.hex is an oracle, never a DUT preload.
 reg [7:0] wanted_payload[0:PAYLOAD_BYTES-1];
 reg boot_verified=0;integer loader_writes=0,boot_i;
 initial $readmemh("payload.hex",wanted_payload);
 always @(physical_memory.memory.U2.writes)if(physical_memory.memory.U2.writes>0)begin
   if(boot_verified)$fatal(1,"TB1 unexpected application SRAM write");
   if(loader_writes>=PAYLOAD_BYTES || physical_memory.memory.U2.writes!=loader_writes+1)
     $fatal(1,"TB1 loader write count");
   if(physical_memory.memory.U2.write_address!==16'h4000+loader_writes)
     $fatal(1,"TB1 loader write address index=%0d got=%h",loader_writes,physical_memory.memory.U2.write_address);
   if(physical_memory.memory.U2.memory[16'h4000+loader_writes]!==wanted_payload[loader_writes])
     $fatal(1,"TB1 loader write data index=%0d",loader_writes);
   loader_writes=loader_writes+1;
 end
 always @(posedge slot_strobe[0])if(slot_reset[0] && !boot_verified)
   $fatal(1,"TB1 IO before reconstructed RAM entry");
 always @(posedge SQ1_PH3)if(SQ1_RESET_n && !boot_verified)begin
   #150;
   if(pc==16'h4000)begin
     if(loader_writes!=PAYLOAD_BYTES)$fatal(1,"TB1 incomplete reconstruction count=%0d",loader_writes);
     for(boot_i=0;boot_i<PAYLOAD_BYTES;boot_i=boot_i+1)
       if(physical_memory.memory.U2.memory[16'h4000+boot_i]!==wanted_payload[boot_i])
         $fatal(1,"TB1 reconstructed payload mismatch index=%0d",boot_i);
     boot_verified=1;
     $display("PASS TB1 ROM reconstruction bytes=%0d writes=%0d pc=%h",PAYLOAD_BYTES,loader_writes,pc);
   end
 end
