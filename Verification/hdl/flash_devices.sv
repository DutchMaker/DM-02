// Read-only SST39SF040 use: CE/OE fixed low, WE fixed high. Not a command model.
module flash_read #(parameter real TACC=70,TSTART=100000,parameter FILE="")
 (input [18:0] address,input ce_n,oe_n,we_n,output [7:0] q);
 reg [7:0] memory[0:524287],value;integer fd,read_count,generation=0;reg ready=0;
 initial begin
   fd=$fopen(FILE,"rb");if(!fd) $fatal(1,"FR1 missing image");
   read_count=$fread(memory,fd);$fclose(fd);
   if(read_count!=524288) $fatal(1,"FR1 image length");
   #(TSTART);ready=1;
 end
 assign q=value;
 always @(we_n) if(we_n===0) $fatal(1,"FR1 write protection");
 task automatic resolve(input integer token,input [18:0] a,input read_enable);
 begin #(TACC);if(generation==token) value=read_enable ? memory[a] : 8'bx;end
 endtask
 always @(address or ce_n or oe_n or ready) begin
   generation=generation+1;value=8'bx;
   fork resolve(generation,address,ready && !ce_n && !oe_n);join_none
 end
endmodule
