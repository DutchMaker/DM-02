"""Freeze selected models and review the ten remaining ACT175 packages."""
from pathlib import Path
from collections import defaultdict
import importlib.util,json,shutil
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import write_json,digest
from dm02.compact_hardware import Circuit,parts
def main():
    sources={}
    for stem in ('m27c1024','um61512a','w27c512','sn74hc377'):
        for p in (HERE.parent/'owned-inventory/sources').glob(stem+'*'):
            dest=HERE/'sources'/p.name;shutil.copyfile(p,dest)
            sources[p.name]=dict(original=str(p.relative_to(r.ROOT)),sha256=digest(p))
    rows=[];used=set()
    for board in json.loads((r.CANDIDATE/'Circuits/KiCad/Compact/candidates/boards.json').read_text()):
        c=Circuit(board);groups=defaultdict(list)
        for ref,cs in c.components.items():
            used.add(cs[0]['value'])
            if cs[0]['value']!='CD74ACT175E':continue
            key=tuple(c.nodes[ref,p] for p in ('9','1'))
            complement=[p for p in ('3','6','11','14') if len(c.nets[c.nodes[ref,p]]['nodes'])>1]
            row=dict(board=board,ref=ref,clock_net=c.nets[key[0]]['labels'],reset_net=c.nets[key[1]]['labels'],used_complement_pins=complement)
            groups[key].append(row);rows.append(row)
        for group in groups.values():assert len([x for x in group if not x['used_complement_pins']])<2,('Remaining compatible 175 pair',group)
    assert len(rows)==10
    selected={k:v for k,v in parts()['devices'].items() if k in used}
    selected['SN74HCT273N']['clock_delay_scope']='42 ns simulation assumption: manufacturer SCLS068H table labels both delay rows CLR. Clarification required for physical clock-to-Q qualification.'
    write_json(HERE/'component-review.json',dict(passed=True,remaining_act175=rows,remaining_compatible_273_pairs=0,
        selected_models=selected,additional_archived_sources=sources,
        scope='No further pair of remaining 175s shares the physical clock/reset nets with unused complemented outputs. Not a global minimum-IC proof.'))
    print('Reviewed ten remaining ACT175s; no directly consolidatable pair')
if __name__=='__main__':main()
