`timescale 1ns/1ps
`include "parameters.vh"
module pilot;
  reg [7:0] address=0, source_q=0, destination=0;
  reg src_clk=0, dst_clk=0, reset=1, inject=0, competing=0;
  reg [7:0] injected=0;
  wire [7:0] rom_q, buffered, data_bus;
  integer mode=0, phase=300, captures=0, i;
  realtime last_data=-10000, last_capture=-10000, rise=-10000, reset_release=-10000;
  realtime launch;
  string vcd;
  // Delay-only behavioural models. There is no reset pin on a 574;
  // reset below is the synthetic controller's capture-inhibit signal.
  always @(posedge src_clk) source_q <= #(`SOURCE_TCO_NS) address;
  assign #(`ROM_ACCESS_NS) rom_q = source_q ^ 8'ha5;
  assign #(`BUFFER_DELAY_NS) buffered = rom_q;
  assign data_bus = inject ? injected : (mode==6 ? {buffered[6:0],buffered[7]} : buffered);
  assign data_bus = competing ? ~buffered : 8'bz;
  always @(negedge reset) reset_release=$realtime;
  always @(data_bus) begin
    if ($realtime-last_capture < `HOLD_NS) $display("VIOLATION HOLD at %0t",$time);
    last_data=$realtime;
  end
  always @(posedge competing) $display("VIOLATION CONTENTION at %0t",$time);
  always @(posedge dst_clk) begin
    rise=$realtime;
    if ($realtime-last_data < `SETUP_NS+`CLOCK_UNCERTAINTY_NS)
      $display("VIOLATION SETUP at %0t",$time);
    // Detect unsettled known-latency path even when the previous value is stable.
    if (phase < `SOURCE_TCO_NS+`ROM_ACCESS_NS+`BUFFER_DELAY_NS+`SETUP_NS+`CLOCK_UNCERTAINTY_NS)
      $display("VIOLATION SETUP at %0t",$time);
    if (reset || $realtime-reset_release < `RESET_GUARD_NS)
      $display("VIOLATION RESET at %0t",$time);
    destination <= data_bus;
    last_capture=$realtime;
    captures=captures+1;
    // Contention is checked separately; do not disguise it as a wiring error.
    #1;
    if (!competing && destination !== (address ^ 8'ha5)) $display("VIOLATION DATA at %0t",$time);
  end
  always @(negedge dst_clk)
    if ($realtime>0 && $realtime-rise < `MINIMUM_PULSE_NS) $display("VIOLATION PULSE at %0t",$time);
  initial begin
    if (!$value$plusargs("MODE=%d",mode)) mode=0;
    if (!$value$plusargs("PHASE=%d",phase)) phase=`CANDIDATE_PHASE_NS;
    if (!$value$plusargs("VCD=%s",vcd)) vcd="pilot.vcd";
    $dumpfile(vcd); $dumpvars(0,pilot);
    #100; reset=0; #100;
    for(i=0;i<8;i=i+1) begin
      address=8'h13+i*17;
      #50; src_clk=1; launch=$realtime;
      fork
        begin
          #(phase); dst_clk=1;
          if(mode==3) #5; else #50;
          dst_clk=0;
        end
        begin
          if(mode==1) begin
            #(phase-40); inject=1; injected=~(address^8'ha5);
            #35; inject=0;
          end
          if(mode==2) begin
            #(phase+1); inject=1; injected=~(address^8'ha5);
            #20; inject=0;
          end
          if(mode==4) begin
            #(phase-40); reset=1; #35; reset=0;
          end
          if(mode==5) begin
            #(phase-60); competing=1; #120; competing=0;
          end
        end
      join
      #100; src_clk=0;
      #(`CLOCK_PERIOD_NS-($realtime-launch)-50);
    end
    #100; $display("DONE captures=%0d",captures); $finish;
  end
endmodule
