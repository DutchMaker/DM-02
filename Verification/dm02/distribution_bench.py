"""FD1 fixture adapter: physical branch monitoring and independent trace checks."""
from dm02.common import VROOT
from designs.distribution_candidate import FACTORIES,LEAVES,RECEIVERS,SOURCES


def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('FD1 fixture anchor changed: '+old)
    return text.replace(old,new,1)


def bench():
    text=(VROOT/'hdl/sequencer_tb.sv').read_text()
    # These monitors are replaced below by seven connector-local guards.
    start=text.index('  always @(data_bus) begin');end=text.index(' task inactive;',start)
    text=text[:start]+'  // FD1_RECEIVER_GUARDS\n '+text[end:]
    declarations=['wire [15:0] clock_leaves;clock_tree distribution(phase,clock_leaves);']
    leaves=[(phase,name) for phase,names in LEAVES.items() for name in names]
    declarations += [f'wire {name}_PH{phase}=clock_leaves[{i}];' for i,(phase,name) in enumerate(leaves)]
    declarations += ['wire [3:0] SQ1_phase={SQ1_PH3,SQ1_PH2,SQ1_PH1,SQ1_PH0};',
        'wire [111:0] df_sources;wire [55:0] df_receivers;wire [5:0] df_control;wire [3:0] df_select;wire fetch1;',
        'data_selector selector(df_control,fetch1,df_select);',
        'data_fabric fabric(df_sources,df_select,df_receivers);']
    declarations += [f'wire [7:0] {name}_DATA=df_receivers[{i*8}+:8];' for i,name in enumerate(RECEIVERS)]
    for name,refs in SOURCES.items():
        ids=list(refs.values());declarations.append(f'wire [{8*len(ids)-1}:0] {name}_SOURCES;')
        declarations += [f'assign df_sources[{8*(source-1)}+:8]={name}_SOURCES[{i*8}+:8];' for i,source in enumerate(ids)]
    text=replace_once(text,'wire [7:0] opcode;','\n'.join(declarations)+'\nwire [7:0] opcode;')
    declarations=['wire [8:0] reset_leaves;reset_tree reset_distribution(reset_n,reset_leaves);']
    declarations += [f'wire {name}_RESET_n=reset_leaves[{i}];' for i,name in enumerate(FACTORIES)]
    text=replace_once(text,'counted_clock source(','\n'.join(declarations)+'\ncounted_clock source(')
    replacements={
        'source(osc,reset_n,':'source(osc,C1_RESET_n,',
        'control_word control(phase[1],cw_ph2,reset_n,':'control_word control(CW1_PH1,cw_ph2,CW1_RESET_n,',
        'sequencer dut(phase,reset_n,':'sequencer dut(SQ1_phase,SQ1_RESET_n,',
        'pc_candidate counter(phase[3],reset_n,':'pc_candidate counter(PC1_PH3,PC1_RESET_n,',
        'memory_io memory(phase[0],phase[2],phase[3],reset_n,':'memory_io memory(ME1_PH0,ME1_PH2,ME1_PH3,ME1_RESET_n,',
        'stack_pointer stack(phase[1],phase[3],reset_n,':'stack_pointer stack(SP1_PH1,SP1_PH3,SP1_RESET_n,',
        'memory_address address(phase[1],phase[3],reset_n,':'memory_address address(MA1_PH1,MA1_PH3,MA1_RESET_n,',
        'timed_alu alu(phase[1],phase[3],reset_n,':'timed_alu alu(AL1_PH1,AL1_PH3,AL1_RESET_n,',
        'general_registers registers(phase[3],reset_n,':'general_registers registers(RG1_PH3,RG1_RESET_n,',
        'always @(posedge phase[2]) if(reset_n && monitor && !finished)':'always @(posedge SQ1_PH2) if(reset_n && monitor && !finished)',
        '@(posedge phase[3]);#100;':'@(posedge SQ1_PH3);#150;',
        'always #62.5 osc=~osc;':'always #125 osc=~osc;',
        'wire halted,fetch0,fetch1,executing':'wire halted,fetch0,executing',
        'cw_pc_n,valid);':'cw_pc_n,valid,df_control);',
        'data_bus,opcode,tstate':'SQ1_DATA,opcode,tstate',
        'pc_address_n,data_bus,address_bus,pc);':'pc_address_n,PC1_DATA,address_bus,pc,PC1_SOURCES);',
        'mar,data_bus,8\'b0,io_data,io_address,io_strobe);':"mar,ME1_DATA,8'b0,io_data,io_address,io_strobe,ME1_SOURCES);",
        'data_bus,stack_address,sp);':'SP1_DATA,stack_address,sp,SP1_SOURCES);',
        'stack_address,data_bus,mar);':'stack_address,MA1_DATA,mar,MA1_SOURCES);',
        'alu_op,data_bus,a,flags,rom_address,result);':'alu_op,AL1_DATA,a,flags,rom_address,result,AL1_SOURCES);',
        'data_bus,{b,c,h,l});':'RG1_DATA,{b,c,h,l},RG1_SOURCES);',
        'assign #(10,10,10) data_bus=peripheral_drive ? settled_data : 8\'bz;':'assign data_bus=SQ1_DATA;',
        '#320;':'#650;',
        'if(!bus_valid && data_bus!==8\'bz) $fatal(1,"SQ bus release");':'if(!bus_valid && df_receivers!==56\'b0) $fatal(1,"DF2 idle DATA must be zero");',
        'DEMO ? 4000000000.0':'DEMO ? 8000000000.0',
        'if(bus_valid && data_bus!==expected_bus)':'if(bus_valid && df_receivers!=={7{expected_bus}})',
        '$fatal(1,"SQ bus cycle=%0d got=%h want=%h",checked,data_bus,expected_bus);':
            '$fatal(1,"DF2 receiver branches cycle=%0d got=%h want=%h",checked,df_receivers,{7{expected_bus}});',
    }
    for old,new in replacements.items():text=replace_once(text,old,new)
    enables={'AL1':"valid && (!load_n[1] || !load_n[6] || !load_n[7])",'PC1':"valid && load_n[12:11]!==2'b11",
             'SQ1':'fetch1','RG1':"valid && load_n[5:2]!==4'b1111",'SP1':"valid && load_n[14:13]!==2'b11",
             'MA1':"valid && load_n[9:8]!==2'b11",'ME1':'valid && !load_n[10]'}
    monitors=[]
    for name in RECEIVERS:
        setup=60 if name in ('SQ1','PC1','ME1') else 40;hold=25 if name=='SQ1' else 40
        monitors.append(f'df_receiver_guard #({setup},{hold}) guard_{name}({name}_PH3,{name}_RESET_n,{enables[name]},{name}_DATA);')
    text=replace_once(text,'  // FD1_RECEIVER_GUARDS','\n'.join(monitors))
    expected={1:'expected_regs[39:32]',2:'expected_regs[31:24]',3:'expected_regs[23:16]',
              4:'expected_regs[15:8]',5:'expected_regs[7:0]',7:"{4'b0,expected_flags}",
              8:'expected_mar[15:8]',9:'expected_mar[7:0]',11:'after_pc[15:8]',12:'after_pc[7:0]',
              13:'expected_sp[15:8]',14:'expected_sp[7:0]'}
    checks=[f'if(df_sources[{8*(source-1)}+:8]!=={value}) $fatal(1,"DF2 private source {source} cycle=%0d got=%h want=%h",checked,df_sources[{8*(source-1)}+:8],{value});' for source,value in expected.items()]
    text=replace_once(text,'checked=checked+1;','\n'.join(checks)+'\nchecked=checked+1;')
    return text+'''
module df_receiver_guard #(parameter real SETUP=40,HOLD=40)
 (input clock,reset_n,enable,input [7:0] data);
 real changed=-10000,captured=-10000,min_setup=1e12,min_hold=1e12;integer captures=0;
 always @(data) begin
   if(reset_n && $realtime-captured<HOLD) $fatal(1,"DF2 receiver hold %m");
   if(reset_n && captures>0 && $realtime-captured<min_hold) min_hold=$realtime-captured;
   changed=$realtime;
 end
 always @(posedge clock) if(reset_n && enable) begin
   if($isunknown(data)) $fatal(1,"DF2 unknown receiver data %m");
   if($realtime-changed<SETUP) $fatal(1,"DF2 receiver setup %m");
   if($realtime-changed<min_setup) min_setup=$realtime-changed;
   captured=$realtime;captures=captures+1;
 end
 final $display("DF2 receiver %m captures=%0d min_setup_ns=%0f min_hold_ns=%0f",captures,min_setup,min_hold);
endmodule
'''
