"""Verify actual native DRC rejects four undersized manufactured features."""
from pathlib import Path
import json
import shutil
import subprocess
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
BOARD=HERE/'CD1-P2-SCREEN-NOT-FOR-FAB.kicad_pcb'


def main():
    folder=HERE/'rule-faults';folder.mkdir(exist_ok=True)
    checks=[]
    for fault,expected in [('narrow-track','track_width'),('small-via','via_diameter'),
                           ('small-drill','drill_out_of_range'),('thin-text','text_thickness')]:
        b=pcb.LoadBoard(str(BOARD))
        if fault=='narrow-track':
            t=next(t for t in b.GetTracks() if not isinstance(t,pcb.PCB_VIA) and t.GetNetname().startswith('/ROOT'))
            t.SetWidth(pcb.FromMM(.14))
        elif fault=='small-via':
            v=next(t for t in b.GetTracks() if isinstance(t,pcb.PCB_VIA));v.SetWidth(pcb.FromMM(.49))
        elif fault=='small-drill':
            v=next(t for t in b.GetTracks() if isinstance(t,pcb.PCB_VIA));v.SetDrill(pcb.FromMM(.2))
        else:
            t=next(t for t in b.GetDrawings() if isinstance(t,pcb.PCB_TEXT) and t.GetLayer()==pcb.F_SilkS)
            t.SetTextThickness(pcb.FromMM(.08))
        path=folder/(fault+'.kicad_pcb');pcb.SaveBoard(str(path),b)
        for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(BOARD.with_suffix(suffix),path.with_suffix(suffix))
        result=subprocess.run(['kicad-cli','pcb','drc',str(path),'--format','json','--output',str(path.with_suffix('.json')),
                              '--severity-all','--refill-zones','--exit-code-violations'],capture_output=True,text=True)
        path.with_suffix('.log').write_text(result.stdout+result.stderr)
        assert result.returncode==5,(fault,result.stdout,result.stderr)
        finding=json.loads(path.with_suffix('.json').read_text())
        types=sorted({v['type'] for v in finding['violations']})
        assert expected in types,(fault,expected,types)
        checks.append(dict(fault=fault,detected=True,expected_type=expected,types=types))
    (HERE/'rule-fault-checks.json').write_text(json.dumps(dict(passed=True,checks=checks),indent=2)+'\n')
    print('Four physical-rule mutations rejected by native DRC')


if __name__=='__main__':main()
