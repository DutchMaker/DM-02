"""Synthetic waveform analysis exercises; never a substitute for pin captures."""
import math


def crossings(points,level):
    result=[]
    for (ta,va),(tb,vb) in zip(points,points[1:]):
        if va<level<=vb:result.append((ta+(tb-ta)*(level-va)/(vb-va),1))
        elif vb<=level<va:result.append((ta+(tb-ta)*(level-va)/(vb-va),0))
    return result


def widths(events):
    return [b[0]-a[0] for a,b in zip(events,events[1:]) if a[1]==1 and b[1]==0]


def analyze(points,supply):
    if len(points)<4 or not all(math.isfinite(v) for p in points for v in p):raise ValueError('Invalid waveform samples')
    if any(b[0]<=a[0] for a,b in zip(points,points[1:])):raise ValueError('Waveform time must increase')
    levels={name:crossings(points,value) for name,value in [('VIL',0.8),('timing',1.5),('VIH',2.0),('half',supply/2),('10pct',supply*.1),('90pct',supply*.9)]}
    rising=[t for t,d in levels['timing'] if d==1];periods=[b-a for a,b in zip(rising,rising[1:])]
    if not periods:raise ValueError('Insufficient clock edges')
    rise10=[t for t,d in levels['10pct'] if d==1];rise90=[t for t,d in levels['90pct'] if d==1]
    fall90=[t for t,d in levels['90pct'] if d==0];fall10=[t for t,d in levels['10pct'] if d==0]
    if not (len(rise10)==len(rise90) and len(fall10)==len(fall90)):raise ValueError('Unpaired waveform transitions')
    edge=max([b-a for a,b in zip(rise10,rise90)]+[b-a for a,b in zip(fall90,fall10)])
    low,high=250/(1+30/1e6),250/(1-30/1e6)
    def span(values):return dict(min=min(values),max=max(values))
    half_rises=[t for t,d in levels['half'] if d==1]
    half_periods=[b-a for a,b in zip(half_rises,half_rises[1:])]
    half_duties=[w/p for w,p in zip(widths(levels['half']),half_periods)]
    # For monotone edges, switching anywhere in VIL..VIH is bracketed by these
    # two widths. Ringing requires direct crossing-count/period investigation.
    guaranteed_high=widths(levels['VIH']);possible_high=widths(levels['VIL'])
    return dict(rising_edges=len(rising),period_ns=span(periods),edge_10_90_max_ns=edge,
        half_supply_duty=span(half_duties),timing_1v5_high_ns=span(widths(levels['timing'])),
        high_width_at_2v_ns=span(guaranteed_high),high_width_at_0v8_ns=span(possible_high),
        nominal_period_screen=all(low-1e-6<=p<=high+1e-6 for p in periods),
        numerical_edge_comparison=dict(CPU_3ns=edge<=3+1e-6,TEXT_6ns=edge<=6+1e-6),
        physical_qualification=False,
        scope='Synthetic 10-90% edge convention; actual ACH edge references unspecified. Numerical comparisons alone establish neither timing-fixture equivalence nor a delay guarantee. Threshold widths presume monotone edges; ringing can cause extra clocks.')


def waveform(supply=5,duty=.5,ppm=0,edge=10,cycles=32,fault=None):
    period=250/(1+ppm/1e6);ramp=edge/.8;points=[(0,0)]
    for i in range(cycles):
        rise=50+i*period;fall=rise+duty*period
        value=0 if fault=='missing-cycle' and i==5 else supply
        points.extend([(rise-ramp/2,0),(rise+ramp/2,value),
                       (fall-ramp/2,value),(fall+ramp/2,0)])
        if fault=='extra-edge' and i==5:
            points.extend([(rise+35,supply),(rise+40,0),(rise+45,supply)])
    points.append((cycles*period+50,0))
    return sorted(points)


def startup(release_ns,valid_since_ns,stable_since_ns,clock_qualified):
    if any(v is None for v in (release_ns,valid_since_ns,stable_since_ns)) or not clock_qualified:return False
    return release_ns-valid_since_ns>=25_000_000 and release_ns>=stable_since_ns


def matrix():
    rows=[]
    for supply in (4.75,5,5.25):
        for duty in (.45,.5,.55):
            for ppm in (-30,0,30):
                for edge in (3,6,10):
                    inputs=dict(supply=supply,duty=duty,ppm=ppm,edge=edge)
                    result=analyze(waveform(**inputs),supply)
                    if not result['nominal_period_screen']:raise ValueError('Synthetic period regression')
                    rows.append(dict(inputs=inputs,analysis=result))
    bad={name:analyze(waveform(fault=name),5) for name in ('extra-edge','missing-cycle')}
    if any(r['nominal_period_screen'] for r in bad.values()):raise ValueError('Undetected clock fault')
    guards=[dict(name='valid',inputs=[25_000_000,0,10_000_000,True],expected=True),
        dict(name='short-guard',inputs=[24_999_999,0,10_000_000,True],expected=False),
        dict(name='brownout-restart',inputs=[25_000_000,15_000_000,20_000_000,True],expected=False),
        dict(name='clock-not-qualified',inputs=[25_000_000,0,10_000_000,False],expected=False)]
    for row in guards:
        row['observed']=startup(*row['inputs'])
        if row['observed']!=row['expected']:raise ValueError('Startup contract regression')
    return dict(origin='synthetic analysis fixtures',cases=rows,clock_faults=bad,startup_cases=guards,
                physical_qualification=False)
