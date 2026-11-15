`timescale 1ns/1ps
module sequencer_tb;
 parameter HARD_ALU=0,CASE_SUITE=0,HARD_REGISTERS=0,HARD_ADDRESS=0,HARD_MEMORY=0,DEMO=0,STARTUP_WAIT_NS=0;
 initial if($test$plusargs("TRACE")) begin $dumpfile("sequencer.vcd");$dumpvars(0,sequencer_tb);end
 reg osc=0,reset_n=1,run=0,resume=0,step=0;
 initial #1 reset_n=0;
  always #(`DM02_OSC_PERIOD_NS/2) osc=~osc;
 wire [3:0] phase,clock_state;wire active,ready,request;
 counted_clock source(osc,reset_n,request,step,phase,active,ready,clock_state);
 wire [7:0] opcode;wire [3:0] tstate,flags;reg [3:0] host_flags=0;
 wire [15:0] word;wire [15:0] address={opcode,tstate,flags};
 wire [14:1] out_n,load_n;wire [12:1] functions;
 wire [4:0] alu_op;wire alu_enable,cw_pc_n,valid,cw_ph2;
 control_word control(phase[1],cw_ph2,reset_n,address,word,out_n,load_n,functions,alu_op,alu_enable,cw_pc_n,valid);
 wire halted,fetch0,fetch1,executing,pc_inc,pc_address_n,mem_n;
 tri [7:0] data_bus;tri [15:0] address_bus;wire [15:0] pc;
 sequencer dut(phase,reset_n,run,resume,valid,functions[1],functions[2],functions[5],cw_pc_n,out_n[10],
   data_bus,opcode,tstate,cw_ph2,request,halted,fetch0,fetch1,executing,pc_inc,pc_address_n,mem_n);
  pc_candidate counter(phase[3],reset_n,pc_inc,load_n[12],load_n[11],out_n[12],out_n[11],HARD_ADDRESS ? 1'b0 : pc_address_n,data_bus,address_bus,pc);

 // Functional peripheral partner, deliberately not electrical qualification.
 // It responds to actual decoded pins, not to expected trace addresses/data.
 reg [7:0] memory[0:65535],host_a=0,host_b=0,host_c=0,host_h=0,host_l=0;wire [7:0] a,b,c,h,l;
 reg [15:0] host_mar=0,host_sp=0,alu_result=0,alu_rom[0:2097151];wire [15:0] mar,sp;
 generate if(HARD_MEMORY) begin : physical_memory
   wire [7:0] io_data,io_address;wire io_strobe;
    memory_io memory(phase[0],phase[2],phase[3],reset_n,mem_n,load_n[10],mar,data_bus,8'b0,io_data,io_address,io_strobe);
    if(DEMO) begin : external_io
      integer expected,observed,count=0,result;reg [7:0] want_address,want_data;
      real changed=-10000,captured=-10000;
      initial begin
        expected=$fopen("io-expected.txt","r");observed=$fopen("io-observed.txt","w");
        if(!expected || !observed) $fatal(1,"ME1 demo IO file");
      end
      always @(io_data or io_address) begin
        if(reset_n && $realtime-captured<40) $fatal(1,"ME1 demo IO hold");
        changed=$realtime;
      end
      always @(posedge io_strobe) if(reset_n) begin
        if($realtime-changed<40) $fatal(1,"ME1 demo IO setup");
        result=$fscanf(expected,"%h %h\n",want_address,want_data);
        if(result!=2 || io_data!==want_data || io_address!==want_address)
          $fatal(1,"ME1 demo IO event %0d got=%h:%h want=%h:%h",count,io_address,io_data,want_address,want_data);
        $fwrite(observed,"%02h %02h\n",io_address,io_data);count=count+1;captured=$realtime;
      end
    end
 end endgenerate
 always @(negedge reset_n) begin host_a=0;host_b=0;host_c=0;host_h=0;host_l=0;host_flags=0;host_mar=0;host_sp=0;alu_result=0;end
 generate if(HARD_ADDRESS) begin : physical_address
   wire [15:0] stack_address;
   stack_pointer stack(phase[1],phase[3],reset_n,functions[3],functions[4],load_n[14],load_n[13],out_n[14],out_n[13],
                       data_bus,stack_address,sp);
   memory_address address(phase[1],phase[3],reset_n,functions[8],fetch0,functions[6],functions[7],
                          load_n[9],load_n[8],out_n[9],out_n[8],address_bus,stack_address,data_bus,mar);
 end else begin : behavioral_address
   assign mar=host_mar;assign sp=host_sp;
 end endgenerate
 generate if(HARD_ALU) begin : physical_alu
   wire [20:0] rom_address;wire [15:0] result;
   timed_alu alu(phase[1],phase[3],reset_n,load_n[1],load_n[6],load_n[7],out_n[1],out_n[6],out_n[7],
                 functions[10],functions[9],functions[12],functions[11],alu_op,data_bus,a,flags,rom_address,result);
 end else begin : behavioral_alu
   assign a=host_a;assign flags=host_flags;
 end endgenerate
 generate if(HARD_REGISTERS) begin : physical_registers
   general_registers registers(phase[3],reset_n,{load_n[5],load_n[4],load_n[3],load_n[2]},
     {out_n[5],out_n[4],out_n[3],out_n[2]},data_bus,{b,c,h,l});
 end else begin : behavioral_registers
   assign b=host_b;assign c=host_c;assign h=host_h;assign l=host_l;
 end endgenerate
 reg [7:0] peripheral_data;reg peripheral_drive;
 integer selected,i,memory_version=0;
 always @(out_n or mem_n or mar or a or b or c or h or l or flags or alu_result or sp or memory_version) begin
   peripheral_data=8'bx;peripheral_drive=0;selected=0;
   for(integer j=1;j<=14;j=j+1) if(!out_n[j]) selected=j;
    if(!mem_n) begin peripheral_data=memory[mar];peripheral_drive=!HARD_MEMORY;end
   else case(selected)
     1:begin peripheral_data=a;peripheral_drive=!HARD_ALU;end
      2:begin peripheral_data=b;peripheral_drive=!HARD_REGISTERS;end
      3:begin peripheral_data=c;peripheral_drive=!HARD_REGISTERS;end
      4:begin peripheral_data=h;peripheral_drive=!HARD_REGISTERS;end
      5:begin peripheral_data=l;peripheral_drive=!HARD_REGISTERS;end
     6:begin peripheral_data=alu_result[7:0];peripheral_drive=!HARD_ALU;end
     7:begin peripheral_data={4'b0,flags};peripheral_drive=!HARD_ALU;end
      8:begin peripheral_data=mar[15:8];peripheral_drive=!HARD_ADDRESS;end
      9:begin peripheral_data=mar[7:0];peripheral_drive=!HARD_ADDRESS;end
      13:begin peripheral_data=sp[15:8];peripheral_drive=!HARD_ADDRESS;end
      14:begin peripheral_data=sp[7:0];peripheral_drive=!HARD_ADDRESS;end
   endcase
 end
 // Model bounded host data settling and release separately to retain blanking.
 wire [7:0] settled_data;
 assign #150 settled_data=peripheral_data;
 assign #(10,10,10) data_bus=peripheral_drive ? settled_data : 8'bz;
 // The current microcode needs address transfer before same-word MEM sampling.
 // Model a bounded early-transfer MAR partner, not a PH3-only MAR register.
  always @(posedge fetch0 or posedge functions[6]) if(reset_n && !HARD_ADDRESS) begin
    #60;host_mar=address_bus;
  end
  always @(posedge functions[7]) if(reset_n && !HARD_ADDRESS) begin #60;host_mar=sp;end
 reg [15:0] next_mar,next_sp;reg [3:0] next_flags;
 always @(posedge phase[3]) if(reset_n && valid) begin
   next_mar=mar;next_sp=sp;next_flags=flags;
   if(functions[3]) next_sp=sp+1'b1;
   if(functions[4]) next_sp=sp-1'b1;
   if(functions[8]) next_mar=next_mar+1'b1;
   if(functions[9]) next_flags[2]=1;
   if(functions[10]) next_flags[0]=1;
   if(functions[11]) next_flags[2]=0;
   if(functions[12]) next_flags[0]=0;
   if(!out_n[6]) next_flags=alu_result[11:8];
   if(!load_n[1]) host_a<=#30 data_bus;
    if(!load_n[2]) host_b<=#30 data_bus;
    if(!load_n[3]) host_c<=#30 data_bus;
    if(!load_n[4]) host_h<=#30 data_bus;
    if(!load_n[5]) host_l<=#30 data_bus;
   if(!load_n[6]) begin
     if(!alu_enable) $fatal(1,"SQ peripheral ALU format");
     alu_result<=#30 alu_rom[{alu_op,a,data_bus}];
   end
   if(!load_n[7]) next_flags=data_bus[3:0];
   if(!load_n[8]) next_mar[15:8]=data_bus;
   if(!load_n[9]) next_mar[7:0]=data_bus;
    if(!load_n[10] && !HARD_MEMORY) begin memory[mar]<=#30 data_bus;memory_version<=#30 memory_version+1;end
   if(!load_n[13]) next_sp[15:8]=data_bus;
   if(!load_n[14]) next_sp[7:0]=data_bus;
    host_mar<=#30 next_mar;host_sp<=#30 next_sp;host_flags<=#30 next_flags;
 end

 integer fd,alu_fd,rc,checked=0,halts=0,cycles=0,paused_cycles,kind,expected_t,bus_valid;
 integer program_cycles,step_cycles,k;
 integer case_fd,case_limit,case_start,case_size,halt_pc,case_count=0;
 real last_data_change=-10000,last_ir_capture=-10000,last_register_capture=-10000,last_address_capture=-10000,last_memory_capture=-10000;
 reg [7:0] expected_op,expected_bus;
 reg [15:0] expected_word,before_pc,after_pc,expected_sp,expected_mar;
 reg [3:0] expected_flags;reg [39:0] expected_regs;
 reg finished=0,monitor=0;
 integer drivers,j;
 always @(out_n or fetch1) begin
   drivers=fetch1===1 ? 1 : 0;
   for(j=1;j<=14;j=j+1) if(out_n[j]===0) drivers=drivers+1;
   if(reset_n && monitor && drivers>1) $fatal(1,"SQ fetch/execute selector overlap");
 end
  always @(data_bus) begin
    if(reset_n && $realtime-last_ir_capture<25) $fatal(1,"SQ IR connector data hold");
    if(reset_n && HARD_REGISTERS && $realtime-last_register_capture<40) $fatal(1,"RG1 connector data hold");
     if(reset_n && HARD_ADDRESS && $realtime-last_address_capture<40) $fatal(1,"Address connector data hold");
     if(reset_n && HARD_MEMORY && $realtime-last_memory_capture<40) $fatal(1,"ME1 connector data hold");
    last_data_change=$realtime;
  end
  always @(posedge phase[3]) if(reset_n && HARD_ADDRESS && valid &&
       (load_n[9:8]!==2'b11 || load_n[14:13]!==2'b11)) begin
    if($realtime-last_data_change<40) $fatal(1,"Address connector data setup");
    last_address_capture=$realtime;
  end
  always @(posedge phase[3]) if(reset_n && HARD_MEMORY && valid && !load_n[10]) begin
    if($realtime-last_data_change<60) $fatal(1,"ME1 connector data setup");
    last_memory_capture=$realtime;
  end
  always @(posedge phase[3]) if(reset_n && HARD_REGISTERS && valid && load_n[5:2]!==4'b1111) begin
    if($realtime-last_data_change<40) $fatal(1,"RG1 connector data setup");
    last_register_capture=$realtime;
  end
 always @(posedge phase[3]) if(reset_n && fetch1) begin
   if($realtime-last_data_change<60) $fatal(1,"SQ IR connector data setup");
   last_ir_capture=$realtime;
 end
 task inactive;
 begin
   if(out_n!==14'h3fff || load_n!==14'h3fff || functions!==0 || fetch0!==0 || fetch1!==0 ||
      pc_inc!==0 || pc_address_n!==1 || mem_n!==1 || alu_enable!==0)
      $fatal(1,"SQ inactive outputs");
 end
 endtask
 // Consume expected cycles only after validity. The first unlatched cycle
 // must do nothing and must not skip fetch0.
 always @(posedge phase[2]) if(reset_n && monitor && !finished) begin
   cycles=cycles+1;
   #320;
   if(!valid) inactive();
   else begin
     rc=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h\n",kind,expected_op,expected_t,expected_word,
                 before_pc,after_pc,expected_flags,expected_sp,expected_mar,expected_regs,expected_bus,bus_valid);
     if(rc!=12) $fatal(1,"SQ expected trace exhausted/malformed %0d",rc);
     if({executing,fetch1,fetch0} !== (kind==0 ? 3'b001 : kind==1 ? 3'b010 : 3'b100))
       $fatal(1,"SQ mode cycle=%0d kind=%0d actual=%b",checked,kind,{executing,fetch1,fetch0});
     if(pc!==before_pc) $fatal(1,"SQ PC before cycle=%0d got=%h want=%h",checked,pc,before_pc);
     if(kind==2 && (opcode!==expected_op || tstate!==expected_t || word!==expected_word))
       $fatal(1,"SQ ROM sequence cycle=%0d op=%h/%h t=%h/%h word=%h/%h",checked,opcode,expected_op,tstate,expected_t,word,expected_word);
     if(bus_valid && data_bus!==expected_bus) $fatal(1,"SQ bus cycle=%0d got=%h want=%h",checked,data_bus,expected_bus);
     if(!bus_valid && data_bus!==8'bz) $fatal(1,"SQ bus release");
     @(posedge phase[3]);#100;
     if(pc!==after_pc || flags!==expected_flags || sp!==expected_sp || mar!==expected_mar || {a,b,c,h,l}!==expected_regs)
       $fatal(1,"SQ state cycle=%0d pc=%h/%h flags=%h/%h sp=%h/%h mar=%h/%h regs=%h/%h",checked,pc,after_pc,flags,expected_flags,sp,expected_sp,mar,expected_mar,{a,b,c,h,l},expected_regs);
     if(kind==1 && opcode!==expected_op) $fatal(1,"SQ fetched IR got=%h want=%h",opcode,expected_op);
     checked=checked+1;
     if(CASE_SUITE ? checked-case_start==case_limit : $feof(fd)) finished=1;
   end
 end
 // HALT stays set after its decoded command is blanked. Complete the current
 // clock cycle, then resume or issue a held single-step without another cycle.
 initial begin
   wait(monitor);
    while(!CASE_SUITE && !DEMO && halts<3) begin
     @(posedge halted);halts=halts+1;#3000;
     if(active!==0 || phase[2]!==0 || phase[3]!==0) $fatal(1,"SQ HALT failed to stop C1");
     inactive();paused_cycles=cycles;#2500;
     if(cycles!=paused_cycles || halted!==1) $fatal(1,"SQ HALT not retained");
     if(halts==1) begin
       // RUN high is insufficient to override HALT. Explicit idle RESUME does.
       resume=1;#300;resume=0;
     end else if(halts==2) begin
       // STEP advances precisely one fetch-address cycle with RUN still high.
       step=1;#6000;
       if(cycles!=paused_cycles+1 || active!==0 || halted!==1) $fatal(1,"SQ held STEP repeats or clears HALT");
       step=0;#500;resume=1;#300;resume=0;
     end else begin resume=1;#300;resume=0;end
   end
 end
  initial begin
    for(i=0;i<65536;i=i+1) memory[i]=0;
    #(STARTUP_WAIT_NS);
   if(!CASE_SUITE) $readmemh("program.hex",memory);
   memory_version=memory_version+1;
   alu_fd=$fopen("alu.bin","rb");if(!alu_fd) $fatal(1,"SQ missing ALU ROM");
   rc=$fread(alu_rom,alu_fd);$fclose(alu_fd);if(rc!=4194304) $fatal(1,"SQ ALU image length");
   fd=$fopen(CASE_SUITE ? "instructions.txt" : "expected.txt","r");if(!fd) $fatal(1,"SQ missing expected trace");
   if(CASE_SUITE) begin
     case_fd=$fopen("cases.txt","r");if(!case_fd) $fatal(1,"SQ missing opcode cases");
     #100;
     while(!$feof(case_fd)) begin
       rc=$fscanf(case_fd,"%h %h %h",case_limit,case_size,halt_pc);
       if(rc!=3) $fatal(1,"SQ malformed opcode case");
       reset_n=0;run=0;finished=1;#1000;
       for(i=0;i<65536;i=i+1) memory[i]=((i*37)^(i>>8)^'ha5)&255;
       for(i=0;i<case_size;i=i+1) begin
         rc=$fscanf(case_fd,"%h\n",memory[i]);if(rc!=1) $fatal(1,"SQ malformed program byte");
       end
       memory['h9001]='hfe;memory['h9002]='h34;memory['h8200]='h83;memory['h8201]=0;
       memory[halt_pc]='he2;memory_version=memory_version+1;
       if(HARD_MEMORY) begin
         for(i=0;i<65536;i=i+1) physical_memory.memory.fixture_byte(i,memory[i]);
         physical_memory.memory.fixture_ready();
       end
       case_start=checked;finished=0;reset_n=1;run=1;monitor=1;
       wait(finished);#2000;
       if(halted!==1 || active!==0 || phase[2]!==0 || phase[3]!==0) $fatal(1,"SQ opcode case did not halt");
       case_count=case_count+1;
     end
     if(case_count==0 || !$feof(fd)) $fatal(1,"SQ incomplete opcode coverage");
     $display("DONE fetched-opcodes cases=%0d cycles=%0d",case_count,checked);$finish;
   end
   #2000;reset_n=1;run=1;monitor=1;
    wait(finished);program_cycles=checked;
    if(DEMO) begin
      #2000;
      if(halted!==1 || active!==0 || phase[2]!==0 || phase[3]!==0) $fatal(1,"ME1 demo did not halt");
      if(!$feof(physical_memory.external_io.expected)) $fatal(1,"ME1 demo missing IO events");
      $fclose(physical_memory.external_io.observed);
      $display("DONE hardware-demo cycles=%0d io=%0d",checked,physical_memory.external_io.count);$finish;
    end
   // Asynchronous reset aborts a running machine and inhibits every output.
   #5;reset_n=0;run=0;#500;inactive();
   if(halted!==0 || pc!==0 || tstate!==0 || executing!==0) $fatal(1,"SQ reset state");
   if(halts!=3) $fatal(1,"SQ HALT coverage");
   #1500;$fclose(fd);fd=$fopen("expected.txt","r");finished=0;reset_n=1;#2000;
   for(k=0;k<13;k=k+1) begin
     step_cycles=cycles;step=1;#6000;
     if(cycles!=step_cycles+1 || active!==0 || phase[2]!==0 || phase[3]!==0) $fatal(1,"SQ stopped-clock STEP protocol");
     inactive();step=0;#500;
   end
   if(checked-program_cycles!=12) $fatal(1,"SQ reset/initial invalid cycle skipped fetch");
   $display("DONE sequencer cycles=%0d halts=%0d stepped=%0d",program_cycles,halts,checked-program_cycles);$finish;
 end
  initial begin #((DEMO ? 4000000000.0 : CASE_SUITE ? 100000000 : 10000000)*`DM02_OSC_PERIOD_NS/125.0);$fatal(1,"SQ watchdog");end
endmodule
