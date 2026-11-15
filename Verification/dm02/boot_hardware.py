"""BL1 fixture transformations; separate ROM/SRAM files and read-only checks."""
import re
from .distribution_bench import replace_once
from .bootloader import ENTRY


def memory_hdl(text):
    text=replace_once(text,'initial $readmemh("program.hex",memory);','initial $readmemh("boot-rom.hex",memory);')
    return replace_once(text,'initial $readmemh("program.hex",memory,0,65535);','initial $readmemh("sram-power-on.hex",memory);')


def testbench(text,coverage):
    image=coverage['image'];full_demo=coverage['full_demo']
    declaration='reg [7:0] loader_target[0:65535];initial $readmemh("loader-target.hex",loader_target);\n'
    text=replace_once(text,'wire [3:0] phase,clock_state;',declaration+'wire [3:0] phase,clock_state;')
    checks=f'''
 reg boot_verified=0;integer boot_index;
 always @(posedge SQ1_PH3) if(SQ1_RESET_n && !boot_verified) begin
   #150;
   if(pc==16'h{ENTRY:04x}) begin
     for(boot_index={ENTRY};boot_index<={image['payload_end']};boot_index=boot_index+1)
       if(physical_memory.memory.U2.memory[boot_index]!==loader_target[boot_index])
         $fatal(1,"BL1 SRAM reconstruction address=%h",boot_index);
     if(physical_memory.memory.U2.writes!={image['expected_loader_sram_writes']})
       $fatal(1,"BL1 unexpected SRAM write count %0d",physical_memory.memory.U2.writes);
     if(physical_memory.external_io.count!=0) $fatal(1,"BL1 unexpected loader IO");
     boot_verified=1;
     $display("DONE BL1 payload_bytes={image['payload_bytes']} writes=%0d",physical_memory.memory.U2.writes);
   end
 end
'''
    text=replace_once(text,' task inactive;',checks+'\n task inactive;')
    if not full_demo:
        replacement='''if(DEMO) begin
       #1;
       if(!boot_verified || pc!==16'h4000) $fatal(1,"BL1 loader did not reach application entry");
       $fclose(physical_memory.external_io.observed);
       $display("DONE hardware-demo cycles=%0d io=0",checked);$finish;
     end'''
        text,count=re.subn(r'if\(DEMO\) begin\s+#2000;.*?\$finish;\s+end',replacement,text,count=1,flags=re.S)
        if count!=1:raise ValueError('BL1 fixture completion anchor changed')
    else:
        text=replace_once(text,'if(!$feof(physical_memory.external_io.expected))',
                          'if(!boot_verified) $fatal(1,"BL1 boot verification missing");\n       if(!$feof(physical_memory.external_io.expected))')
    return text


def verify_log(log,coverage):
    image=coverage['image']
    loader=f'DONE BL1 payload_bytes={image["payload_bytes"]} writes={image["expected_loader_sram_writes"]}'
    final=f'DONE hardware-demo cycles={coverage["microcycles"]} io={coverage["io_events"]}'
    lines=log.splitlines()
    return dict(boot_verified=lines.count(loader)==1,cycles_and_io_verified=lines.count(final)==1,
                passed=lines.count(loader)==1 and lines.count(final)==1)
