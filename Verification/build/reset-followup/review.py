"""Reproduce supervisor screening from archived manufacturer limits.

The 4.5 V lower boundary applies only to a future machine with an oscillator
qualified down to 4.5 V. C1's installed ECS part requires 4.75 V.
"""
from decimal import Decimal as D
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent


def review():
    hashes={}
    for name,sidecar in [('mcp131x-21985D.pdf','source.json'),
                         ('tps3890.pdf','tps3890-source.json'),
                         ('tps3890-q1.pdf','tps3890-q1-source.json')]:
        want=json.loads((HERE/sidecar).read_text())['sha256']
        got=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
        if got!=want:raise ValueError('Manufacturer source changed: '+name)
        hashes[name]=got
    supply_min=D('4.75');candidate_floor=D('4.5');accuracy=D('.01')
    rows=[]
    # Separate positive and negative limits are specified. Hysteresis must
    # not be added a second time to the positive threshold table entry.
    for suffix,fall,rise in [('50','4.80','4.828'),('50G','4.65','4.677'),('50L','4.40','4.425')]:
        n,p=D(fall),D(rise);nmin=n*(1-accuracy);pmax=p*(1+accuracy)
        rows.append(dict(mpn=f'TPS3890{suffix}QDSERQ1',negative_nominal_v=n,positive_nominal_v=p,
                         negative_min_v=nmin,negative_max_v=n*(1+accuracy),
                         positive_min_v=p*(1-accuracy),positive_max_v=pmax,
                         release_headroom_v=supply_min-pmax,
                         static_falling_headroom_v=nmin-candidate_floor,
                         static_window_passed=nmin>candidate_floor and pmax<supply_min,
                         source='tps3890-q1.pdf pages 3 and 5; -40..125 C, VDD 1.5..5.5 V'))
    g=next(r for r in rows if r['mpn']=='TPS389050GQDSERQ1')
    # Explicit exploratory capacitor envelope, not a selected passive.
    cmin=D('47e-9')*D('.8');cmax=D('47e-9')*D('1.2')
    residual=D('.1');leakage=D('10e-9')
    tmin=cmin*(D('1.17')-residual)/(D('1.35e-6')+leakage)
    tmax=cmax*D('1.29')/(D('.90e-6')-leakage)
    mcp_rise=D('4.669')+D('.276')
    return dict(source_hashes=hashes,scope='Component screening only; no reset circuit or acceptance gate is qualified.',
                boundaries=dict(valid_supply_min_v=supply_min,candidate_operating_floor_v=candidate_floor,
                                installed_C1_oscillator_min_v=D('4.75'),
                                note='The candidate 4.5 V floor requires a separately qualified oscillator variant and machine supply review.'),
                mcp1316=dict(mpn='MCP1316T-46LE/OT',status='rejected for this supply window',
                             release_max_at_25c_v=mcp_rise,release_headroom_v=supply_min-mcp_rise,
                             negative_min_over_temperature_v=D('4.485'),
                             reset_delay_ms=[140,200,280],watchdog_typ_ms=1600,
                             source='mcp131x-21985D.pdf pages 5, 7, 9 and 39',
                             notes=['Hysteresis bounds are at 25 C only; no numeric full-temperature hysteresis guarantee extracted.',
                                    'The B delay code is a custom short-delay combination. Page 39 says 1.6 ms typical, while page 9 says 1.4 ms typical; it cannot cover the ACH 10 ms startup maximum.',
                                    'Assertion delay and output slew are typical-only.']),
                tps3890_variants=rows,
                tps389050g=dict(status='static threshold candidate; dynamic qualification open',
                               package='DSE WSON-6, 1.5 x 1.5 mm',
                               pins={'1':'SENSE','2':'GND','3':'MR_n','4':'VDD','5':'CT','6':'RESET_n (open drain)'},
                               lifecycle='Active/Production in archived package addendum; TI product page also says ACTIVE.',
                               stock='TI public page says out of stock; authorized-distributor availability unverified.',
                               startup_illustration=dict(cap_nominal_f=D('47e-9'),effective_cap_min_f=cmin,effective_cap_max_f=cmax,
                                                         assumed_ct_residual_max_v=residual,assumed_external_leakage_abs_a=leakage,
                                                         charge_time_min_s=tmin,charge_time_max_s=tmax,
                                                         margin_above_10ms_s=tmin-D('.010'),
                                                         scope='Conditional CT charging term only. Effective capacitance, leakage and discharge residual are assumptions. Nominal-only internal timing is excluded; no complete reset-delay guarantee.'),
                               brownout=dict(assertion_max_us=None,
                                             reason='Page 5 gives only nominal SENSE-to-RESET delays at 5% overdrive. A maximum shallow-droop assertion delay is missing.',
                                             response_budgets=[dict(fall_rate_mv_per_us=rate,
                                                                    total_time_before_4_5v_us=g['static_falling_headroom_v']*1000/rate)
                                                               for rate in map(D,('.1','1','10','100'))],
                                             budget_scope='Available rail-decay time only; detection, conditioning, distribution and write termination must all fit. No response maximum is assumed.'),
                               open=['Exact timing capacitor and pull-up selection with temperature/bias/leakage bounds',
                                     'Schmitt conditioning, low-voltage power-on behaviour, loaded output slew and reset distribution',
                                     'Clock-valid startup and recovery/removal at every receiver',
                                     'Bounded shallow-brownout response and interrupted SRAM/IO writes',
                                     'WSON footprint, assembly, procurement and physical validation']))


if __name__=='__main__':
    result=review()
    (HERE/'review.json').write_text(json.dumps(result,indent=2,default=lambda v:float(v))+'\n')
    for row in result['tps3890_variants']:
        print(row['mpn'],'static_window_passed=',row['static_window_passed'],
              'fall_min=',row['negative_min_v'],'rise_max=',row['positive_max_v'])
    print('MCP1316 maximum release at 25 C:',result['mcp1316']['release_max_at_25c_v'])
    print('TPS389050G complete reset qualification: OPEN')
