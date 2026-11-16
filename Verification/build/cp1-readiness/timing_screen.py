"""CP1-R2 selected-path screening, not exhaustive timing closure.

Explicit CP1 topology and selected DIP bounds; never calls the FD1 budget.
All delays are ns. Capture-side contamination delay is conservatively zero.
"""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=HERE.parent/'cp1-hct273'
HDL=BASE/'candidate/Verification/build/compact/c1-cases0'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    lock=json.loads((ROOT/'Verification/targets/cp1/lock.json').read_text())
    sources={}
    for name in ('C1','CW1','SQ1','AL1','RG1','ME1','BF1','DT1'):
        p=HDL/(name+'.sv');key=str(p.relative_to(HERE.parent))
        assert lock['artifacts'][key]==sha(p)
        sources[key]=sha(p)
    # HDL receipts identify actual pin-derived paths. Strings deliberately fail
    # closed if the archived model/topology changes.
    checks={
        'C1':['clock_ff #(13,13,2,2,1,1,1) U1','n[39]=n[49] & n[19]'],
        'CW1':['cw574 #(45,25,5,20) U3','cp_control_rom #(100) U1'],
        'SQ1':['cw574 #(45,25,5,20) U6','n[37]=n[10] & n[42]','n[36]=n[7] & n[68]'],
        'ME1':['cp_sram #(15,10,15,12,9,7) U2','bufif0 #(74,74,50) U9_0'],
        'BF1':['bufif0 #(74,74,50) U104_0','bufif0 #(74,74,50) U105_0'],
        'AL1':['cp273 #(42,3) U2','cw574 #(45,25,5,20) U8'],
    }
    for board,strings in checks.items():
        text=(HDL/(board+'.sv')).read_text()
        for s in strings:assert s in text,(board,s)
    # Worst clock gate values at 50 pF avoid relying on the 15 pF allocation.
    paths=[
        dict(id='clock-next-state',window='half',terms={
            'root inverter':8.5,'clock buffer':9.5,'routing/jitter allocation':2,
            'ACT175 clock-Q':13,'AHC32':8.5,'AHC08':9,'ACT175 setup':2},
            topology='C1 U1 Q -> U4 OR -> U5 AND -> U2 D; opposite clock edges'),
        dict(id='control-address',window=3,terms={
            'DT1 two buffers':19,'SQ1 clock buffer':9.5,'HCT161 clock-Q':75,
            'M27C1024 access':100,'HCT574 setup':25,'route allocation':10},
            topology='PH0 -> DT1 -> SQ1 U4 tstate -> CW1 U1 ROM -> U3/U4 at PH1'),
        dict(id='alu-result',window=4,terms={
            'DT1 two buffers':19,'AL1 two clock buffers':19,'operand clock-Q envelope':42,
            'M27C322 access':100,'HCT574 setup':25,'route allocation':10},
            topology='PH3 -> DT1 -> AL1 U2/U6/U7 -> U1 ROM -> U8/U9 at PH1'),
        dict(id='word-before-enable',window=1,terms={
            'DT1 two buffers':19,'CW1 clock buffer':9.5,'HCT574 clock-Q':45,
            'format AND':9,'format inverter':8.5,'route allocation':10},
            topology='PH1 -> DT1 -> CW1 U3/U4 -> format gating, before PH2'),
        dict(id='fetch-sram-to-ir',window=3,terms={
            'DT1 two buffers':19,'SQ1 fetch ANDs':18,'SQ1 invert':8.5,'SQ1 mem merge':9,
            'ME1 read inverter':8.5,'ME1 read AND/NAND':18,'SRAM access envelope':15,
            'ME1 read muxes':24,'three HCT245 stages':222,
            'SQ1 input NAND mux':18,'IR setup':25,'route allocation':10},
            topology='PH2 -> SQ1 FETCH1/MEM_n -> ME1 U2 -> U5/U6 or U7/U8 -> U9 -> BF1 U104 -> U105 -> SQ1 U6 at PH3'),
        dict(id='execute-sram-to-ir-mux-envelope',window=3,terms={
            'DT1 two buffers':19,'SQ1 execute gate':9,'CW1 phase gate':9,
            'CW1 invert':8.5,'HCT154 decode':53,'SQ1 mem merge':9,
            'ME1 read inverter':8.5,'ME1 read AND/NAND':18,'SRAM access envelope':15,
            'ME1 read muxes':24,'three HCT245 stages':222,
            'receiver data/enable allowance':46.5,'route allocation':10},
            topology='PH2 -> SQ1 CW_PH2 -> CW1 U5 MEM_out -> SQ1 MEM_n -> ME1 SRAM/mux/U9 -> BF1 U104/U105 -> register receiver at PH3'),
        dict(id='same-word-mar-to-bootrom-control-branch',window=3,terms={
            'DT1 two buffers':19,'SQ1 execute gate':9,'CW1 phase gate':9,
            'CW1 inverter':8.5,'HCT154 decode':53,'CW1 function merge':9,
            'MA1 transfer OR pair':20,'transfer window AND':9,'preset OR':10,
            'preset inverter':8.5,'reset AND':9,'transfer fanout buffer':9.5,
            'HCT191 asynchronous load-Q':50,'W27C512 access':45,
            'ME1 read muxes':24,'three HCT245 stages':222,
            'connector setup contract':40,'route allocation':10},
            topology='PH2 -> CW1 PC_TRANSFER -> MA1 transfer/preset -> U3..U6 -> ME1 U1 ROM/mux/U9 -> BF1 U104/U105 -> SP1 load',
            condition='TRANSFER_WINDOW and preset data already ready. A later window can only worsen this bound; complete window/min-delay closure remains required.'),
    ]
    # The last row bounds the common receiver data side (buffer+mux+setup),
    # not each destination's counter/load control logic. Those need full closure.
    rows=[]
    for mhz in (2,4,5,6,8):
        period=1000/mhz/(1+30/1e6)
        for p in paths:
            available=.37*period if p['window']=='half' else p['window']*period-(13+9.5+10)
            required=sum(p['terms'].values())
            rows.append(dict(oscillator_mhz=mhz,microcycle_hz=mhz*1e6/8,path=p['id'],
                             available_ns=available,required_ns=required,margin_ns=available-required))
    loads=json.loads((BASE/'loads.json').read_text())
    selected=[r for r in loads if any(d['part']=='SN74HCT245N' for d in r['drivers'])]
    result=dict(revision='CP1-R2',scope='Selected max-delay screens, not exhaustive setup/hold or physical qualification.',
        physical_qualification=False,input_hashes=sources,paths=paths,rows=rows,
        assumptions=dict(receiver_duty_min=.37,ppm=30,phase_output_spread_ns=32.5,
            phase_spread_basis='ACT175 13 + AHCT244 9.5 + allocated route/jitter 10; earliest capture is zero delay',
            device_bounds='Selected datasheet/model bounds apply only at cited supply, slew and load conditions',
            topology_exclusions=['counter asynchronous load and ripple control','SRAM write/turnaround hazards',
                'minimum-delay/hold','reset and asynchronous inputs','BF1 enable reconvergence']),
        hct245_driven_nets=len(selected),hct245_disable_load_excess=[r for r in selected if r['allocated_load_pf']>50])
    out=HERE/'timing-screen.json'
    assert not out.exists(),'Preserve completed screen'
    out.write_text(json.dumps(result,indent=2)+'\n')
    for r in rows:print(r['oscillator_mhz'],r['path'],round(r['margin_ns'],3))

if __name__=='__main__':main()
