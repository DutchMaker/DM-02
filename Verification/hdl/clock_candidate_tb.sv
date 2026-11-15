`timescale 1ns/1ps
`include "parameters.vh"
module clock_candidate_tb;
  reg osc=0,reset_n=0,request=0,step=0;
  wire [3:0] phase,state;
  wire active,ready;
  counted_clock dut(osc,reset_n,request,step,phase,active,ready,state);
  real duty=0.5,ppm=0,period,reset_release=-100000;
  real last_edge[0:3],last_rise[0:3];
  integer launches=0,completed=0,steps=0,button_steps=0,stops=0,resets=0,transitions=0,transfers=0;
  integer i,j,old_launch,old_completed;
  reg [3:0] previous=0;
  reg previous_valid=0;
  reg [3:0] states[0:7];
  reg [7:0] address=8'h13,source_q=0,expected=0;
  wire [7:0] rom_q,data_bus;
  reg transfer_valid=0;
  real last_data=-10000,last_capture=-10000;
  // The same bounded path as the original pilot, now clocked by pin-derived
  // phase outputs rather than independently scheduled ideal clocks.
  assign #(`ROM_ACCESS_NS) rom_q=source_q^8'ha5;
  assign #(`BUFFER_DELAY_NS) data_bus=rom_q;
  always @(negedge phase[2]) address=address+8'h31;
  always @(negedge reset_n) transfer_valid=0;
  always @(posedge phase[2]) begin
    if(reset_n && $realtime-reset_release>1500) begin
      source_q<=#(`SOURCE_TCO_NS) address;
      expected=address^8'ha5;transfer_valid=1;
    end
  end
  always @(data_bus) begin
    if(reset_n && $realtime-last_capture<`HOLD_NS) $fatal(1,"pilot hold");
    last_data=$realtime;
  end
  always @(posedge phase[3]) begin
    if(reset_n && $realtime-reset_release>1500 && transfer_valid) begin
      if($realtime-last_data<`SETUP_NS+`CLOCK_UNCERTAINTY_NS) $fatal(1,"pilot setup");
      if(data_bus!==expected) $fatal(1,"pilot data");
      last_capture=$realtime;transfers=transfers+1;transfer_valid=0;
    end
  end

  function automatic [3:0] next_state(input [3:0] value);
    case(value)
      0:next_state=1; 1:next_state=3; 3:next_state=7; 7:next_state=15;
      15:next_state=14; 14:next_state=12; 12:next_state=8; 8:next_state=0;
      default:next_state=4'bx;
    endcase
  endfunction

  initial begin
    if(!$value$plusargs("DUTY=%f",duty)) duty=0.5;
    if(!$value$plusargs("PPM=%f",ppm)) ppm=0;
    period=125.0/(1+ppm/1000000.0);
    forever begin #(period*(1-duty)); osc=1; #(period*duty); osc=0; end
  end
  always @(posedge reset_n) reset_release=$realtime;
  always @(negedge reset_n) previous_valid=0;
  // Sample after the maximum oscillator->conditioner->branch->Q->buffer delay,
  // but before the next oscillator edge at the worst supported duty ratio.
  always @(negedge osc) begin
    #48;
    if(reset_n && $realtime-reset_release>1500) begin
      if(phase !== {state[3],state[0],~state[3],~state[0]})
        $fatal(1,"phase polarity/pin mapping: state=%b phase=%b",state,phase);
      if(active !== (state[0]|state[3])) $fatal(1,"active/idle mapping");
      if(ready !== 1'b1) $fatal(1,"reset release not complete");
      if(previous_valid) begin
        if(previous==0) begin
          if(state!=0 && state!=1) $fatal(1,"invalid start state %b",state);
        end else if(state !== next_state(previous))
          $fatal(1,"truncated or corrupted cycle: %b -> %b",previous,state);
        transitions=transitions+1;
      end
      previous=state;previous_valid=1;
    end else previous_valid=0;
  end

  generate for(genvar p=0;p<4;p=p+1) begin : monitors
    initial begin last_edge[p]=-100000;last_rise[p]=-100000; end
    always @(phase[p]) begin
      if(reset_n && $realtime-reset_release>1500 && last_edge[p]>reset_release+1500 &&
         $realtime-last_edge[p]<468)
        $fatal(1,"runt phase pulse channel=%0d width=%0f",p,$realtime-last_edge[p]);
      last_edge[p]=$realtime;
    end
    always @(posedge phase[p]) begin
      if(reset_n && $realtime-reset_release>1500) begin
        if(p==2) launches=launches+1;
        if(p==3) completed=completed+1;
      end
      last_rise[p]=$realtime;
    end
    if(p==1 || p==3) begin : capture
      always @(posedge phase[p]) begin
        if(reset_n && $realtime-reset_release>1500 && last_rise[p-1]>reset_release+1500 &&
           ($realtime-last_rise[p-1]<343 || $realtime-last_rise[p-1]>407))
          $fatal(1,"launch/capture phase interval %0d = %0f",p,$realtime-last_rise[p-1]);
      end
    end
  end endgenerate

  task idle_check;
    begin
      #3000;
      if(state!==0 || active!==0 || phase!==4'b0011 || ready!==1)
        $fatal(1,"failed to stop at complete-cycle boundary");
    end
  endtask

  task step_cycle(input real offset);
    begin
      old_launch=launches;old_completed=completed;
      request=1;
      wait(active===1);#(offset);request=0;
      wait(active===0);idle_check;
      if(launches-old_launch!=1 || completed-old_completed!=1)
        $fatal(1,"single-cycle handshake repeated/lost: %0d/%0d",launches-old_launch,completed-old_completed);
      steps=steps+1;
    end
  endtask

  initial begin
    $dumpfile("clock.vcd");$dumpvars(0,clock_candidate_tb);
    states[0]=0;states[1]=1;states[2]=3;states[3]=7;
    states[4]=15;states[5]=14;states[6]=12;states[7]=8;
    #5;reset_n=0;#1500;reset_n=1;idle_check;
    for(i=0;i<16;i=i+1) begin #(i*7+1);step_cycle(i*12); end
    // Test the physical pending latch, including a button held across cycles.
    for(i=0;i<16;i=i+1) begin
      old_launch=launches;old_completed=completed;
      #(i*7+1);step=1;#(2000+i*31);step=0;idle_check;
      if(launches-old_launch!=1 || completed-old_completed!=1)
        $fatal(1,"single-step pending latch lost or repeated");
      button_steps=button_steps+1;
    end
    old_launch=launches;old_completed=completed;
    step=1;wait(active===1);#30;step=0;#30;step=1;#30;step=0;idle_check;
    if(launches-old_launch!=1 || completed-old_completed!=1)
      $fatal(1,"STEP while active must be ignored");
    button_steps=button_steps+1;
    // Hold request high: the frequency must stay at oscillator/8.
    request=1;#5000;
    for(i=0;i<20;i=i+1) begin : rate
      real edge_time;
      @(posedge phase[0]);edge_time=$realtime;
      @(posedge phase[0]);
      if($realtime-edge_time<8*period-0.1 || $realtime-edge_time>8*period+0.1)
        $fatal(1,"continuous divide ratio");
    end
    request=0;idle_check;
    // Stop requests at each Johnson state and several sub-cycle offsets.
    for(i=0;i<8;i=i+1) begin
      for(j=0;j<4;j=j+1) begin
        request=1;wait(state===1);wait(state===states[i]);
        #(j*13+1);request=0;idle_check;stops=stops+1;
      end
    end
    if(launches!=completed) $fatal(1,"unmatched launch/capture after drain");
    // Reset is an explicit abort; normal-cycle pulse requirements are suspended.
    // Receivers must be inhibited by the system reset protocol.
    for(i=0;i<8;i=i+1) begin
      request=1;wait(state===1);wait(state===states[i]);
      #(i*3+1);reset_n=0;request=0;#1000;
      if(state!==0) $fatal(1,"asynchronous reset did not clear phase state");
      #(i*11+1);reset_n=1;idle_check;resets=resets+1;
      step_cycle(20);
    end
    // RUN already high during reset must start a complete first cycle.
    for(i=0;i<4;i=i+1) begin : startup
      real first_launch;
      reset_n=0;request=1;#(1100+i*17);reset_n=1;
      @(posedge phase[2]);first_launch=$realtime;
      if(ready!==1) $fatal(1,"started before reset sequencing completed");
      @(posedge phase[3]);
      if($realtime-first_launch<343 || $realtime-first_launch>407)
        $fatal(1,"first launch/capture interval");
      request=0;idle_check;
    end
    if(transfers<100) $fatal(1,"insufficient pilot transfers");
    $display("DONE counted-clock steps=%0d stops=%0d resets=%0d button_steps=%0d transitions=%0d transfers=%0d idle_phases=%0d",steps,stops,resets,button_steps,transitions,transfers,phase);
    $finish;
  end
  initial begin #2000000; $fatal(1,"clock test timed out"); end
endmodule
