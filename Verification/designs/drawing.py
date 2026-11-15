"""Small deterministic legacy-sheet writer for discrete candidate circuits."""
from dm02.legacy import library


class Drawing:
    def __init__(self,title,revision,comments,row_step=2200,page=('A1',33110,23386)):
        self.lines=['EESchema Schematic File Version 4','EELAYER 29 0','EELAYER END',
                    f'$Descr {page[0]} {page[1]} {page[2]}','Sheet 1 1',f'Title "{title}"','Date "2026-11-14"',
                    f'Rev "{revision}"','Comp "DM-02"']
        self.lines += [f'Comment{i+1} "{text}"' for i,text in enumerate((comments+['']*4)[:4])]+['$EndDescr']
        self.serial=0
        self.row_step=row_step
        self.height=page[2]

    def part(self,lib,ref,value,unit,nets,footprint):
        i=self.serial;self.serial+=1;x=2000+(i%10)*3100;y=1900+(i//10)*self.row_step
        pins=[p for p in library(lib.split(':')[0])[lib.split(':')[1]]['pins'] if p['unit'] in (0,unit) and p['convert'] in (0,1)]
        if set(nets)!={p['number'] for p in pins}:raise ValueError('Incomplete pins: '+ref)
        self.lines.extend(['$Comp',f'L {lib} {ref}',f'U {unit} 1 {0x69E00000+i:08X}',f'P {x} {y}',
                           f'F 0 "{ref}" H {x+100} {y+300} 50 0000 L CNN',f'F 1 "{value}" H {x+100} {y+200} 50 0000 L CNN',
                           f'F 2 "{footprint}" H {x} {y} 50 0001 C CNN',f'\t{unit} {x} {y}','\t1 0 0 -1','$EndComp'])
        for p in pins:
            px,py=x+p['x'],y-p['y'];net=nets[p['number']]
            if py>self.height-886:raise ValueError('Drawing exceeds sheet')
            if net is None:self.lines.append(f'NoConn ~ {px} {py}')
            else:self.lines.extend([f'Text Label {px} {py} 0 39 ~ 0',net])

    def text(self):return '\n'.join(self.lines+['$EndSCHEMATC'])+'\n'
