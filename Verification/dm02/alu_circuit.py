"""Pin-derived ALU HDL with common-clock capture and flag hold/control logic."""
import struct
from .common import ROOT, BUILD, command, digest, evidence, write_json
from .legacy import read_sheet, connectivity, function_number
from .alu import expected


SCOPE=('KiCad-derived operand/operation registers, ROM interface, flag data/feedback selection, '
       'four stored flags, phase-qualified C/Z controls and two bus drivers. All storage clocks '
       'come from the CLOCK_PH3 connector net; controls change during its low phase. '
       'Zero-delay logical device models and an ideal connector clock; no physical phase-generator, '
       'setup/hold, recovery/removal, OE handover, reset sequencing or electrical qualification.')


class Datapath:
    def __init__(self,sheet=None):
        self.sheet=sheet or read_sheet(ROOT/'Circuits/KiCad/ALU/ALU.sch')
        self.nets=connectivity(self.sheet)
        self.nodes={tuple(p):i for i,n in enumerate(self.nets) for p in n['nodes']}
        self.labels={label:i for i,n in enumerate(self.nets) for label in n['labels']}
        self.parts={(c['ref'],c['unit']):c for c in self.sheet['components']}
        for ref,symbol in [('U1','74HC74'),('U2','74HC74'),('U3','M27C322'),
                           ('U5','74LS377'),('U6','74LS377'),('U7','74LS377'),
                           ('U8','74HCT244'),('U9','74LS245'),('U13','74LS245'),('U14','74LS125')]:
            if self.parts[ref,1]['lib_id'].split(':')[-1]!=symbol:
                raise ValueError('Unsupported ALU symbol: '+ref)

    def pin(self,ref,name,unit=1):
        p=next(p for p in self.parts[ref,unit]['pins'] if p['name']==name)
        return self.nodes[ref,p['number']]

    def vector(self,ref,prefix,width,unit=1):
        return '{'+','.join(f'n[{self.pin(ref,prefix+str(b),unit)}]' for b in reversed(range(width)))+'}'

    def routes(self):
        errors=[];checked=0
        def check(actual,want,description):
            nonlocal checked
            checked+=1
            if actual!=want: errors.append(description)
        for ref,prefix,width in [('U5','DATA',8),('U6','DATA',8),('U7','ALUFUNC',5)]:
            for b in range(8):
                check(self.pin(ref,f'D{b}'),self.labels[f'{prefix}{b}' if b<width else 'GND'],f'{ref} D{b}')
            check(self.pin(ref,'~E'),self.labels['~A_load' if ref=='U5' else '~ALU_load'],ref+' enable')
            check(self.pin(ref,'CP'),self.labels['CLOCK_PH3'],ref+' clock')
        for b in range(21):
            ref,bit=('U6',b) if b<8 else ('U5',b-8) if b<16 else ('U7',b-16)
            check(self.pin('U3',f'A{b}'),self.pin(ref,f'Q{bit}'),f'ROM A{b}')
        for name in ('~CE','~OE'): check(self.pin('U3',name),self.labels['GND'],'ROM '+name)
        for b in range(8):
            check(self.pin('U13',f'A{b}'),self.pin('U3',f'D{b}'),f'result {b}')
            for ref in ('U9','U13'):
                check(self.pin(ref,f'B{b}'),self.labels[f'DATA{b}'],f'{ref} bus {b}')
            check(self.pin('U9',f'A{b}'),self.labels[f'FLAGS{b}' if b<4 else 'GND'],f'packed F {b}')
        for ref,oe in [('U9','~F_out'),('U13','~ALU_out')]:
            check(self.pin(ref,'A->B'),self.labels['5V'],ref+' direction')
            check(self.pin(ref,'CE'),self.labels[oe],ref+' OE')
        for b,(ref,unit) in enumerate([('U1',1),('U2',1),('U1',2),('U2',2)]):
            check(self.pin('U8',f'1A{b}'),self.pin('U3',f'D{b+8}'),f'raw flag {b}')
            check(self.pin('U8',f'2A{b}'),self.labels[f'DATA{b}'],f'bus flag {b}')
            for group in (1,2):
                check(self.pin('U8',f'{group}Y{b}'),self.pin(ref,'D',unit),f'flag D {b} source {group}')
            check(self.pin(ref,'Q',unit),self.labels[f'FLAGS{b}'],f'stored flag {b}')
            check(self.pin(ref,'C',unit),self.labels['CLOCK_PH3'],f'flag clock {b}')
            oe,inp,out=[(1,2,3),(4,5,6),(10,9,8),(13,12,11)][b]
            check(self.nodes['U14',str(inp)],self.labels[f'FLAGS{b}'],f'feedback input {b}')
            check(self.nodes['U14',str(out)],self.pin(ref,'D',unit),f'feedback output {b}')
            check(self.nodes['U14',str(oe)],self.labels['FLAG_NEW_DATA'],f'feedback enable {b}')
        for group,label in [(1,'~ALU_out'),(2,'~F_load')]:
            check(self.pin('U8',f'{group}OE'),self.labels[label],f'flag select {group}')
        # An unrelated connector bus must never become a ROM operand source.
        for b in range(8):
            checked+=1
            if self.pin('U3',f'A{b+8}')==self.labels[f'A{b}']: errors.append(f'address bus alias {b}')
        for b in range(4):
            checked+=1
            if self.pin('U3',f'D{b+8}')==self.labels[f'FLAGS{b}']: errors.append(f'raw/stored flag alias {b}')
        return dict(checked=checked,errors=errors)

    def hdl(self,stimulus=None):
        def pin(ref,name,unit=1): return f'n[{self.pin(ref,name,unit)}]'
        def bus(prefix,width): return '{'+','.join(f'n[{self.labels[prefix+str(b)]}]' for b in reversed(range(width)))+'}'
        v=self.vector
        lines=['`timescale 1ns/1ps','module alu_slice;',f'tri [{len(self.nets)-1}:0] n;',
               'reg [7:0] data_in=0; reg drive=1;',
               'reg [4:0] operation=0; reg [15:0] external_address=0;',
               'reg phase=0; reg [3:0] commands=15;',
               'reg a_load_n=1, alu_load_n=1, f_load_n=1, alu_out_n=1, f_out_n=1;',
               'wire [7:0] data_bus; wire [3:0] flags; wire [20:0] rom_address;',
               'wire [15:0] rom_data; reg [15:0] rom [0:2097151];',
               'reg [36:0] vectors [0:8191]; reg [36:0] test_vector;',
               'integer i,j,k,checks=0,command_checks=0; reg [3:0] saved,want_flags; reg [15:0] want;',
               f'assign data_bus={bus("DATA",8)}; assign flags={bus("FLAGS",4)};',
               f'assign rom_address={v("U3","A",21)};',
               'assign rom_data=rom[rom_address];',
               f'assign {v("U3","D",16)}=({pin("U3","~CE")} || {pin("U3","~OE")}) ? 16\'bz : rom_data;']
        for label,value in [('GND',"1'b0"),('5V',"1'b1"),('~ALU_load','alu_load_n'),
                            ('~F_load','f_load_n'),('~ALU_out','alu_out_n'),('~F_out','f_out_n'),
                            ('~A_load','a_load_n'),('CLOCK_PH3','phase'),('~FCLR_c','commands[0]'),
                            ('~FCLR_z','commands[1]'),('~FSET_c','commands[2]'),('~FSET_z','commands[3]')]:
            lines.append(f'assign n[{self.labels[label]}]={value};')
        for b in range(8): lines.append(f'assign n[{self.labels[f"DATA{b}"]}]=drive ? data_in[{b}] : 1\'bz;')
        for prefix,width,source in [('ALUFUNC',5,'operation'),('A',16,'external_address')]:
            for b in range(width): lines.append(f'assign n[{self.labels[prefix+str(b)]}]={source}[{b}];')
        for ref in ('U5','U6','U7'):
            lines.append(f'reg377 {ref} ({v(ref,"D",8)}, {pin(ref,"CP")}, {pin(ref,"~E")}, {v(ref,"Q",8)});')
        for b in range(4):
            for group in (1,2):
                lines.append(f'assign {pin("U8",f"{group}Y{b}")}={pin("U8",f"{group}OE")} ? 1\'bz : {pin("U8",f"{group}A{b}")};')
        for ref in ('U9','U13'):
            lines.append(f'buffer245 {ref} ({v(ref,"A",8)}, {v(ref,"B",8)}, {pin(ref,"A->B")}, {pin(ref,"CE")});')
        for oe,inp,out in [(1,2,3),(4,5,6),(10,9,8),(13,12,11)]:
            lines.append(f'assign n[{self.nodes["U14",str(out)]}]=n[{self.nodes["U14",str(oe)]}] ? 1\'bz : n[{self.nodes["U14",str(inp)]}];')
        for c in self.sheet['components']:
            kind=function_number(c['lib_id'].split(':')[-1])
            if kind not in ('04','32'): continue
            inputs=[self.nodes[c['ref'],p['number']] for p in c['pins'] if p['kind']=='I']
            outputs=[self.nodes[c['ref'],p['number']] for p in c['pins'] if p['kind']=='O']
            if not inputs and not outputs: continue
            if len(outputs)!=1 or len(inputs)!=(1 if kind=='04' else 2): raise ValueError('Unsupported ALU gate')
            expr='~n['+str(inputs[0])+']' if kind=='04' else ' | '.join(f'n[{i}]' for i in inputs)
            lines.append(f'assign n[{outputs[0]}]={expr};')
        for ref,unit in [('U1',1),('U1',2),('U2',1),('U2',2)]:
            lines.append(f'ff74 {ref}_{unit} ({pin(ref,"D",unit)}, {pin(ref,"C",unit)}, {pin(ref,"~S",unit)}, {pin(ref,"~R",unit)}, {pin(ref,"Q",unit)}, {pin(ref,"~Q",unit)});')
        lines.append('''
task tick;
  begin #2; phase=1; #2; phase=0; #2; end
endtask
initial begin
  $readmemh("rom.hex",rom); $readmemh("vectors.hex",vectors);
  f_load_n=0; tick; f_load_n=1;
  for(i=0;i<8192;i=i+1) begin
    test_vector=vectors[i]; want=test_vector[15:0];
    alu_out_n=1; f_out_n=1; alu_load_n=1; f_load_n=1; drive=1;
    saved=flags;
    operation=test_vector[36:32]; data_in=test_vector[31:24]; a_load_n=0;
    tick; a_load_n=1;
    data_in=test_vector[23:16]; alu_load_n=0; tick; alu_load_n=1;
    if(flags !== saved) $fatal(1,"flags changed during operand capture");
    // Changes after capture must not alter the latched operands/operation.
    operation=~operation; data_in=~data_in; external_address=i^16'ha55a; tick;
    if(rom_address !== test_vector[36:16]) $fatal(1,"ROM address route/hold %0d",i);
    external_address=~external_address; #2;
    if(rom_address !== test_vector[36:16]) $fatal(1,"ROM address route/hold %0d",i);
    if(rom_data !== want) $fatal(1,"ROM payload %0d",i);
    drive=0; alu_out_n=0; #2;
    if(data_bus !== want[7:0]) $fatal(1,"result bus %0d",i);
    tick;
    if(flags !== want[11:8]) $fatal(1,"ALU flag capture %0d",i);
    alu_out_n=1; #2;
    if(data_bus !== 8'bz) $fatal(1,"result bus release");
    f_out_n=0; #2;
    if(data_bus !== {4'b0,want[11:8]}) $fatal(1,"packed flags %0d",i);
    f_out_n=1; #2;
    if(data_bus !== 8'bz) $fatal(1,"flag bus release");
    checks=checks+1;
  end
  // Every bus byte crossed with every raw flag nibble. A changing raw ROM
  // output must neither bypass the flag storage nor corrupt a bus flag load.
  operation=1; drive=1; data_in=0; a_load_n=0; alu_load_n=0; tick;
  a_load_n=1; alu_load_n=1;
  for(i=0;i<256;i=i+1) begin
    for(j=0;j<16;j=j+1) begin
      rom[rom_address]={4'b0,j[3:0],8'ha5};
      data_in=i; f_load_n=0; tick;
      if(flags !== i[3:0]) $fatal(1,"bus flag load %0d/%0d",i,j);
      f_load_n=1; saved=flags; rom[rom_address]=16'hffff; tick;
      if(flags !== saved) $fatal(1,"raw flags bypass storage");
      drive=0; f_out_n=0; #2;
      if(data_bus !== {4'b0,i[3:0]}) $fatal(1,"bus flag roundtrip");
      f_out_n=1; drive=1; #2; checks=checks+1;
    end
  end
  // Commands are inactive outside PH3 and affect only the selected C/Z bit.
  for(i=0;i<16;i=i+1) begin
    for(j=0;j<4;j=j+1) begin
      drive=1; data_in=i; f_load_n=0; tick; f_load_n=1;
      commands=15^(1<<j); #2;
      if(flags !== i[3:0]) $fatal(1,"flag command outside phase");
      want_flags=i;
      case(j)
        0: want_flags[0]=0; 1: want_flags[2]=0;
        2: want_flags[0]=1; 3: want_flags[2]=1;
      endcase
      tick;
      if(flags !== want_flags) $fatal(1,"flag command %0d/%0d",i,j);
      commands=15; tick;
      if(flags !== want_flags) $fatal(1,"flag command hold");
      command_checks=command_checks+1;
    end
  end
  // Feedback and opposing-driver cases exercise resolved nets, not a software
  // multiplexer that would hide contention or choose one input by priority.
  drive=0; rom[rom_address]=16'h0f00;
  alu_out_n=0; f_load_n=0; #2;
''')
        for b,(ref,unit) in enumerate([('U1',1),('U2',1),('U1',2),('U2',2)]):
            lines.append(f'if({pin(ref,"D",unit)} !== 1\'bx) $fatal(1,"flag contention {b}");')
        lines.append('alu_out_n=1; f_load_n=1; #2;')
        for ref,unit in [('U1',1),('U2',1),('U1',2),('U2',2)]:
            lines.append(f'if({pin(ref,"D",unit)} !== {pin(ref,"Q",unit)}) $fatal(1,"flag feedback hold");')
        lines.append('''
  drive=1; data_in=0; f_load_n=0; tick; f_load_n=1; drive=0;
  rom[rom_address]=16'h0fff;
  alu_out_n=0; f_out_n=0; #2;
  if(data_bus !== 8'bx) $fatal(1,"result/flag opposing drivers not observed");
  alu_out_n=1; f_out_n=1; #2;
  if(data_bus !== 8'bz) $fatal(1,"final bus release");
  $display("DONE checks=%0d command_checks=%0d contention_checks=2",checks,command_checks); $finish;
end
endmodule
module reg377(input [7:0] d,input clk,enable_n,output reg [7:0] q);
  always @(posedge clk) if(!enable_n) q<=d;
endmodule
module ff74(input d,clk,set_n,clear_n,output reg q,output q_n);
  always @(posedge clk or negedge set_n or negedge clear_n)
    if(!set_n && !clear_n) q<=1'bx;
    else if(!clear_n) q<=0;
    else if(!set_n) q<=1;
    else q<=d;
  assign q_n=~q;
endmodule
module buffer245(inout [7:0] a,b,input direction,enable_n);
  assign b=(!enable_n && direction) ? a : 8'bz;
  assign a=(!enable_n && !direction) ? b : 8'bz;
endmodule
''')
        text='\n'.join(lines)
        if stimulus is not None:
            start=text.index('initial begin\n');end=text.index('\nendmodule\n',start)
            text=text[:start]+stimulus+text[end:]
        return text


def simulate(circuit,folder,stimulus=None,done='DONE checks=12288 command_checks=64 contention_checks=2'):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'slice.sv').write_text(circuit.hdl(stimulus))
    code,log=command(['iverilog','-g2012','-o',folder/'slice.vvp',folder/'slice.sv'])
    if code: raise RuntimeError(log)
    code,output=command(['vvp',folder/'slice.vvp'],cwd=folder,timeout=180)
    log+=output; (folder/'slice.log').write_text(log)
    return code==0 and done in log,log


def fixtures(folder):
    words=struct.unpack('<2097152H',b''.join((BUILD/f'alu/alu{i}.rom').read_bytes() for i in range(8)))
    (folder/'rom.hex').write_text(''.join(f'{w:04x}\n' for w in words))
    rows=[]
    for op in range(32):
        for a in range(256):
            b=(a*73+op*19)&255
            rows.append(f'{(op<<32)|(a<<24)|(b<<16)|expected(op,a,b):010x}\n')
    (folder/'vectors.hex').write_text(''.join(rows))


def run():
    from .logisim_alu import trace
    circuit=Datapath();folder=BUILD/'alu/circuit';folder.mkdir(parents=True,exist_ok=True)
    fixtures(folder);ok,log=simulate(circuit,folder);routes=circuit.routes()
    reference=trace();write_json(folder/'logisim-reference.json',reference)
    write_json(folder/'pins.json',dict(source=circuit.sheet['source'],source_sha256=digest(ROOT/circuit.sheet['source']),
                                     nets=circuit.nets,routes=routes,scope=SCOPE,
                                     vectors=8192,flag_roundtrips=4096,command_checks=64,contention_checks=2))
    return evidence('alu-circuit','Schematic-derived ALU data path','pass' if ok and not routes['errors'] and not reference['errors'] else 'fail',
                    f'8,192 operand/function vectors, 4,096 flag round trips, 64 phase-qualified flag commands, two opposing-driver checks; {len(routes["errors"])} pin-route errors.',
                    artifacts=['alu/circuit/pins.json','alu/circuit/slice.sv','alu/circuit/slice.log',
                               'alu/circuit/rom.hex','alu/circuit/vectors.hex','alu/circuit/logisim-reference.json'],limitation=SCOPE)
