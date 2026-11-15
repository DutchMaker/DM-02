"""FD1 pin-derived models with explicit sheet paths and no global patches."""
from pathlib import Path
from .common import VROOT
from .legacy import read_sheet
from .alu_hardware import Circuit as Alu
from .address_hardware import Circuit as Logic
from designs.distribution_candidate import FACTORIES,SOURCES,RECEIVERS

PARTS=VROOT/'distribution-parts.json'


def load_boards(folder):
    folder=Path(folder).resolve()
    return {name:factory(read_sheet(folder/f'{"Data" if name in SOURCES or name=="CW1" else "Reset"}-{name}.sch'))
            for name,factory in FACTORIES.items()}


def exported_hdl(c,corner,name):
    text=c.hdl(corner)
    if name=='CW1':
        width=6;bindings=[f'assign df_export[{b}]={c.n("J900",b+3)};' for b in range(6)]
    elif name in SOURCES:
        ids=list(SOURCES[name].values());width=8*len(ids)
        bindings=[f'assign df_export[{i*8+b}]={c.n(f"J{900+s}",b+3)};' for i,s in enumerate(ids) for b in range(8)]
    else:return text
    assert ');' in text and '\nendmodule' in text
    return text.replace(');',f',output [{width-1}:0] df_export);',1).replace('\nendmodule','\n'+'\n'.join(bindings)+'\nendmodule',1)


class Distribution(Logic):
    def __init__(self,path):Alu.__init__(self,read_sheet(Path(path).resolve()),parts_file=PARTS)

    def module(self,ports,bindings,corner):
        return '\n'.join(['`timescale 1ns/1ps',ports,f'tri n[0:{len(self.nets)-1}];',
                          f'assign n[{self.labels["5V"]}]=1;assign n[{self.labels["GND"]}]=0;',
                          *bindings,*self.logic_hdl(corner),'endmodule'])


class ClockTree(Distribution):
    def hdl(self,corner=0):
        bindings=[f'assign {self.n("J1",b+3)}=phase[{b}];' for b in range(4)]
        bindings += [f'assign leaves[{b}]={self.n("J2",b+3)};' for b in range(16)]
        return self.module('module clock_tree(input [3:0] phase,output [15:0] leaves);',bindings,corner)


class ResetTree(Distribution):
    def hdl(self,corner=0):
        bindings=[f'assign {self.n("J1",3)}=reset_n;']
        bindings += [f'assign leaves[{b}]={self.n("J2",b+3)};' for b in range(9)]
        return self.module('module reset_tree(input reset_n,output [8:0] leaves);',bindings,corner)


class Selector(Distribution):
    def hdl(self,corner=0):
        bindings=[f'assign {self.n("J1",b+3)}=control[{b}];' for b in range(6)]
        bindings += [f'assign {self.n("J1",9)}=fetch1;']
        bindings += [f'assign select[{b}]={self.n("J2",b+3)};' for b in range(4)]
        return self.module('module data_selector(input [5:0] control,input fetch1,output [3:0] select);',bindings,corner)


class Fabric(Distribution):
    def hdl(self,corner=0):
        bindings=[f'assign {self.n(f"J{s+1}",b+3)}=sources[{s*8+b}];' for s in range(14) for b in range(8)]
        bindings += [f'assign receivers[{i*8+b}]={self.n(f"J{i+21}",b+3)};' for i in range(len(RECEIVERS)) for b in range(8)]
        bindings += [f'assign {self.n("J30",b+3)}=select[{b}];' for b in range(4)]
        return self.module('module data_fabric(input [111:0] sources,input [3:0] select,output [55:0] receivers);',bindings,corner)
