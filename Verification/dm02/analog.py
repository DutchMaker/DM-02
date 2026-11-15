"""Manufacturer-model PILOT-03 evidence plus the retained RC sensitivity study."""
import itertools
import re
from .common import BUILD, command, evidence, write_json


def sensitivity():
    folder=BUILD/'analog'
    folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    # At 25ns after the transition: setup-window voltage and threshold crossing.
    for r,c,v in itertools.product((30,100,200),(50,150,1000),(3.84,4.75,5.25)):
        name=f'r{r}-c{c}-v{v}'
        deck=f'''* Illustrative Thevenin driver; no nonlinear device or Schmitt feedback
Vdrive src 0 PULSE(0 {v} 10n 1n 1n 500n 1000n)
Rdriver src out {r}
Cload out 0 {c}p
.tran 0.2n 800n
.measure tran capture_v FIND v(out) AT=35n
.measure tran low_v FIND v(out) AT=750n
.control
run
wrdata {name}.dat v(out)
quit
.endc
.end
'''
        (folder/(name+'.cir')).write_text(deck)
        code,log=command(['ngspice','-b',name+'.cir'],cwd=folder)
        (folder/(name+'.log')).write_text(log)
        def measured(key):
            m=re.search(rf'{key}\s*=\s*([\d.eE+\-]+)',log)
            if code or not m:
                raise RuntimeError(f'Missing ngspice measurement {name}/{key}: {log[-500:]}')
            return float(m[1])
        high,low=measured('capture_v'),measured('low_v')
        rows.append(dict(name=name,r_ohm=r,c_pf=c,source_v=v,capture_v=high,low_v=low,
                         passes_thresholds=high>=2.0 and low<=0.8))
    nominal=next(x for x in rows if x['r_ohm']==100 and x['c_pf']==50 and x['source_v']==4.75)
    overload=next(x for x in rows if x['r_ohm']==200 and x['c_pf']==1000 and x['source_v']==3.84)
    qualified=nominal['passes_thresholds'] and not overload['passes_thresholds']
    write_json(folder/'sweep.json',rows)
    return evidence('analog-rc','Loaded-output RC sensitivity','limited' if qualified else 'fail',
                    f'{len(rows)} ngspice cases; nominal passes and overloaded case is detected: {qualified}.',
                    rows=rows,artifacts=['analog/sweep.json',f"analog/{nominal['name']}.cir",f"analog/{nominal['name']}.dat"],
                     limitation='Linear RC bounds only. Not validation of the 1nF HCT14 clock, drive-current ratings, ringing or hardware operation.')


def run():
    from .loaded_output import run as loaded_output
    return [sensitivity(),loaded_output()]
