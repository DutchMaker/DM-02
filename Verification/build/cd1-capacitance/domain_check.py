"""Check artificial boundary influence on the isolated comparison geometry."""
from pathlib import Path
import json
from field import cross_section

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'numerical-results.json').read_text())
baseline = next(r for r in data['scenarios'] if r['kind']=='isolated-thin' and r['parameters']['er']==4.8)
rows = [dict(box_mm=12., **{k:v for k,v in baseline.items() if k not in ('parameters','label','kind')})]
for box in (24.,48.):
    result = cross_section(er=4.8, thickness=0., coplanar=False, box=box, minimum=.00125, growth=1.08)
    rows.append(dict(box_mm=box, **result))
    print(box, result['capacitance_pf_per_mm'], flush=True)
final_change = abs(rows[-1]['capacitance_pf_per_mm']/rows[-2]['capacitance_pf_per_mm']-1)
total_change = abs(rows[-1]['capacitance_pf_per_mm']/rows[0]['capacitance_pf_per_mm']-1)
assert final_change < .005 and total_change < .02
(HERE / 'domain-check.json').write_text(json.dumps(dict(passed=True, rows=rows,
    last_step_relative_change=final_change, production_to_largest_relative_change=total_change), indent=2)+'\n')
print('Isolated-line box check passes:',total_change,'relative change from production box',flush=True)
