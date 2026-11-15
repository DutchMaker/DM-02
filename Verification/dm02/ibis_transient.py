"""Two-fixture IBIS extraction and independently integrated load experiments.

Vendor inputs, coefficients and derived SPICE decks stay in a private cache.
Public results are numerical checks, not a redistributed device model.
"""
import subprocess
import sys
from datetime import datetime,timezone
import numpy as np
from scipy.integrate import solve_ivp
from .ibis_factors import audit, coefficients


def factors(data, edge, col, step_ns=0.01):
    times = sorted(set([i*step_ns*1e-9 for i in range(round(50/step_ns)+1)] +
        [row[0] for wave in data['waves'] if wave['edge'] == edge for row in wave['rows']]))
    rows = []
    for t in times:
        ku, kd, determinant = coefficients(data, edge, col, t)
        assert abs(determinant) > 1e-10, 'Ill-conditioned two-fixture extraction'
        assert all(np.isfinite(v) for v in (ku, kd))
        rows.append([t, ku, kd])
    return np.array(rows)


def spice(data, factor, edge, col, work, name, capacitance_pf=0, fixture_v=0,
          fixture_r=1000, package=None, offset_ns=0, stop_ns=55, step_ns=.01, disabled=False, die_cap_pf=4, initial_rail=False):
    vcc = data['voltage'][col-1]
    row = next(w for w in data['waves'] if w['edge'] == edge and w['params']['V_fixture'+('', '_min', '_max')[col-1]] == fixture_v)
    initial = row['rows'][0][col] if fixture_r else (0 if edge == 'rising' else vcc)
    if initial_rail:
        initial=0 if edge=='rising' else vcc
    lines = ['* Two-fixture IBIS behavioural experiment; local derived model', f'Cdie die 0 {die_cap_pf}p IC={initial}']
    if disabled:
        factor=factor.copy(); factor[:,1:]=0
    for i, pin in enumerate(('ku', 'kd'), 1):
        points = [(0, factor[0,i])] if offset_ns else []
        points.extend((t+offset_ns*1e-9, value) for t, value in factor[:,[0,i]])
        lines.append(f'V{pin} {pin} 0 PWL('+' '.join(f'{t:.15g} {v:.15g}' for t,v in points)+')')
    for i, (key, variable, multiplier) in enumerate((('Pullup', f'{vcc}-v(die)', 'v(ku)'),
        ('Pulldown', 'v(die)', 'v(kd)'), ('GND Clamp', 'v(die)', '1'), ('POWER Clamp', f'{vcc}-v(die)', '1'))):
        expr = audit.pwl_expression(data['tables'][key], col, variable)
        lines.append(f'B{i} die 0 I=({multiplier})*({expr})')
    if package:
        lines.extend([f'Rpkg die lead {package[0]}', f'Lpkg lead out {package[1]} IC=0',
                      f'Cpkg out 0 {package[2]} IC={initial}'])
        out = 'out'
    else:
        out = 'die'
    if capacitance_pf:
        lines.append(f'Cload {out} 0 {capacitance_pf}p IC={initial}')
    if fixture_r:
        lines.extend([f'Vfixture fixture 0 {fixture_v}', f'Rload {out} fixture {fixture_r}'])
    output = work/(name+'.dat')
    if output.exists(): output.unlink()
    lines.extend(['.options reltol=1e-6 abstol=1e-11 vntol=1e-8 method=gear', '.control',
        f'tran {step_ns}n {stop_ns}n 0 {step_ns}n uic',
        f'wrdata {output} v({out}) v(die)', 'quit', '.endc', '.end'])
    path = work/(name+'.cir'); path.write_text('\n'.join(lines)+'\n')
    result = subprocess.run(['ngspice','-b',str(path)],capture_output=True,text=True,timeout=60)
    (work/(name+'.log')).write_text(result.stdout+result.stderr)
    assert result.returncode == 0 and output.exists(), result.stdout+result.stderr
    waveform = np.loadtxt(output)
    assert waveform.ndim==2 and waveform.shape[1]==4 and np.all(np.isfinite(waveform)), 'Invalid SPICE samples'
    assert waveform[-1,0] >= stop_ns*1e-9*.999, result.stdout+result.stderr
    return waveform[:,[0,1]], waveform[:,[0,3]]


def reference_comparison(data, wave, col, simulated):
    original = np.array(wave['rows'])
    times = np.linspace(0,50e-9,10001)
    want = np.interp(times, original[:,0],original[:,col])
    got = np.interp(times,simulated[:,0],simulated[:,1])
    threshold=2.0 if wave['edge']=='rising' else .8
    expected=audit.crossing(wave['rows'],col,threshold,wave['edge']=='rising')
    measured=audit.crossing(simulated.tolist(),1,threshold,wave['edge']=='rising')
    return dict(max_difference_v=float(np.max(abs(want-got))),rms_difference_v=float(np.sqrt(np.mean((want-got)**2))),
                threshold_difference_ns=abs(measured-expected)*1e9)


def measure(waveform, edge, start_ns, end_ns):
    if (edge not in ('rising','falling') or not np.all(np.isfinite([start_ns,end_ns])) or not np.all(np.isfinite(waveform)) or
            waveform.ndim!=2 or waveform.shape[1]!=2 or len(waveform)<2 or
            not np.all(np.diff(waveform[:,0])>0) or end_ns<start_ns or
            waveform[0,0]>start_ns*1e-9 or waveform[-1,0]<end_ns*1e-9):
        raise ValueError('Invalid or incomplete capture-window waveform')
    selected=waveform[(waveform[:,0]>=start_ns*1e-9)&(waveform[:,0]<=end_ns*1e-9),1]
    selected=np.append(selected,np.interp([start_ns*1e-9,end_ns*1e-9],waveform[:,0],waveform[:,1]))
    threshold=2.0 if edge=='rising' else .8
    valid=bool(np.min(selected)>=threshold if edge=='rising' else np.max(selected)<=threshold)
    t=audit.crossing(waveform.tolist(),1,threshold,edge=='rising')
    return dict(passed=valid,window_min_v=float(np.min(selected)),window_max_v=float(np.max(selected)),
                stable_threshold_ns=None if t is None else t*1e9,
                setup_margin_ns=None if t is None else start_ns-t*1e9)


def package_pin(text):
    sections=audit.sections(text)
    index=next(i for i,s in enumerate(sections) if s['key']=='Component' and s['value']=='HCT245_N')
    pins=next(s for s in sections[index:] if s['key']=='Pin')
    fields=next(row.split() for _,row in pins['rows'] if row.split()[0]=='18')
    assert fields[1:3]==['B1','HCT245_IO']
    return tuple(map(audit.number,fields[3:]))


def independent_ode(data,factor,edge,package,capacitance_pf,offset_ns,stop_ns=500,fixture_r=None,fixture_v=0):
    """Integrate die capacitor + package R/L + external capacitor with Radau.

    State is [die volts, pin volts, package milliamps], time is nanoseconds.
    This never reads a SPICE voltage or uses a SPICE initial solution.
    """
    tables={key:np.array(rows) for key,rows in data['tables'].items()}
    supply=data['voltage'][0]
    cdie=data['capacitance'][0]*1e12
    resistance,inductance,cpackage=package
    inductance*=1e9
    cout=capacitance_pf+cpackage*1e12
    times=factor[:,0]*1e9+offset_ns
    def rhs(t,y):
        die,out,ipkg=y
        ku=np.interp(t,times,factor[:,1]); kd=np.interp(t,times,factor[:,2])
        def iv(key,x):
            table=tables[key];return np.interp(x,table[:,0],table[:,1])*1000
        idie=ku*iv('Pullup',supply-die)+kd*iv('Pulldown',die)
        idie+=iv('GND Clamp',die)+iv('POWER Clamp',supply-die)
        external=1000*(out-fixture_v)/fixture_r if fixture_r else 0
        return [-(idie+ipkg)/cdie,(ipkg-external)/cout,1000*(die-out-resistance*ipkg/1000)/inductance]
    initial=[0,0,0] if edge=='rising' else [supply,supply,0]
    result=solve_ivp(rhs,[0,stop_ns],initial,method='Radau',rtol=1e-7,
        atol=[1e-9,1e-9,1e-7],max_step=.05,dense_output=True)
    assert result.success,result.message
    times=np.arange(0,stop_ns+.005,.01)
    return np.column_stack((times*1e-9,result.sol(times)[1]))


def experiment(text,contract,private,output_folder):
    """Fresh simulation, correlation, independent integration and fault cases."""
    data=audit.model_data(text)
    package=package_pin(text)
    private.mkdir(parents=True,exist_ok=True)
    output_folder.mkdir(parents=True,exist_ok=True)
    results=[]
    for col in (1,2):
        for edge in ('rising','falling'):
            factor=factors(data,edge,col)
            for wave in data['waves']:
                if wave['edge'] != edge: continue
                fixture=wave['params']['V_fixture'+('', '_min', '_max')[col-1]]
                name=f'correlation-{col}-{edge}-{fixture}'
                actual,_=spice(data,factor,edge,col,private,name,fixture_v=fixture)
                compared=reference_comparison(data,wave,col,actual)
                print(name,compared,flush=True)
                results.append(dict(case=name,**compared))
    loads=[]; independent=[]; refinements=[]
    for edge in ('rising','falling'):
        factor=factors(data,edge,1)
        for fault in ('normal','overload','premature-capture','late-launch','disabled'):
            name=edge+'-'+fault
            cap=contract['faults']['overload_pf'] if fault=='overload' else contract['total_external_load_pf']
            offset=contract['faults']['late_shape_launch_ns'] if fault=='late-launch' else contract['shape_launch_ns']
            start,end=contract['valid_window_start_ns'],contract['valid_window_end_ns']
            if fault=='premature-capture':
                start=contract['faults']['premature_capture_ns']-contract['setup_ns']-contract['uncertainty_ns']
                end=contract['faults']['premature_capture_ns']+contract['hold_ns']+contract['uncertainty_ns']
            fixture_v=0 if edge=='rising' else contract['supply_v']
            fixture_r=contract['opposing_fixture_resistance_ohm']
            actual,_=spice(data,factor,edge,1,private,name,capacitance_pf=cap,fixture_r=fixture_r,fixture_v=fixture_v,
                package=package,offset_ns=offset,stop_ns=500,disabled=fault=='disabled',initial_rail=True)
            result=dict(case=name,edge=edge,fault=fault,capacitance_pf=cap,window_start_ns=start,window_end_ns=end,
                fixture_v=fixture_v,fixture_r_ohm=fixture_r,shape_launch_ns=offset,driver_enabled=fault!='disabled',
                **measure(actual,edge,start,end))
            # Only computed loaded-output traces are published; neither raw
            # vendor fixtures nor extracted switching coefficients are copied.
            output=output_folder/'traces';output.mkdir(exist_ok=True)
            times=np.arange(0,500.01,.05)*1e-9
            np.savetxt(output/(name+'.csv'),np.column_stack((times*1e9,np.interp(times,actual[:,0],actual[:,1]))),
                delimiter=',',header='time_ns,output_v',comments='')
            print(result,flush=True); loads.append(result)
            if fault in ('normal','overload'):
                ode=independent_ode(data,factor,edge,package,cap,offset,fixture_r=fixture_r,fixture_v=fixture_v)
                difference=float(np.max(abs(ode[:,1]-np.interp(ode[:,0],actual[:,0],actual[:,1]))))
                independent.append(dict(case=name,max_voltage_difference_v=difference,
                    measured=measure(ode,edge,start,end)))
                print('Independent',independent[-1],flush=True)
            if fault=='normal':
                refined,_=spice(data,factors(data,edge,1,.005),edge,1,private,name+'-refined',
                    capacitance_pf=cap,fixture_r=fixture_r,fixture_v=fixture_v,package=package,
                    offset_ns=offset,stop_ns=500,step_ns=.005,initial_rail=True)
                measured=measure(refined,edge,start,end)
                refinements.append(dict(case=name,threshold_difference_ns=abs(measured['stable_threshold_ns']-result['stable_threshold_ns']),
                    measured=measured))
                print('Refinement',refinements[-1],flush=True)
    conversion_faults=[]
    wave=next(w for w in data['waves'] if w['edge']=='falling' and w['params']['V_fixture']==5)
    corrupted,_=spice(data,factors(data,'falling',1),'falling',1,private,
        'conversion-fault-wrong-cdie',fixture_v=5,die_cap_pf=40)
    conversion_faults.append(dict(fault='die-capacitance-times-ten',
        **reference_comparison(data,wave,1,corrupted)))
    rejected=[]
    for edge in ('rising','falling'):
        try:
            factors(data,edge,3)
        except (ZeroDivisionError,AssertionError) as error:
            rejected.append(dict(corner='max',edge=edge,reason='Singular/ill-conditioned two-fixture extraction',exception=type(error).__name__))
    import scipy
    output=dict(created_at=datetime.now(timezone.utc).isoformat(),model_sha256=audit.MODEL_HASH,
        package_pin_rlc=list(package),
        tools=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,
            ngspice=subprocess.run(['ngspice','--version'],capture_output=True,text=True,check=True).stdout),
        correlation=results,loads=loads,independent=independent,refinements=refinements,
        rejected_corners=rejected,conversion_faults=conversion_faults)
    return output
