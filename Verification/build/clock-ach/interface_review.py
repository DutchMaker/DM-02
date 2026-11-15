"""Static receiver and nominal footprint screen with explicit missing bounds."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'sandbox/Verification'))
from dm02.sexpr import parse


def main():
    source=Path.home()/'Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Oscillator.pretty/Oscillator_DIP-8.kicad_mod'
    dest=HERE/'footprint/Oscillator_DIP-8.kicad_mod';dest.parent.mkdir(exist_ok=True)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if dest.exists():assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
    else:shutil.copyfile(source,dest)
    pads={}
    for item in parse(dest.read_text()):
        if not isinstance(item,list) or not item or item[0]!='pad':continue
        fields={x[0]:x[1:] for x in item[4:] if isinstance(x,list)}
        pads[item[1]]=dict(at_mm=list(map(float,fields['at'][:2])),drill_mm=float(fields['drill'][0]),
            size_mm=list(map(float,fields['size'])),type=item[2],shape=item[3])
    assert {p:r['at_mm'] for p,r in pads.items()}=={'1':[0.,0.],'4':[7.62,0.],'5':[7.62,-7.62],'8':[0.,-7.62]}
    assert all(p['drill_mm']==.8 for p in pads.values())
    dc=dict(oscillator_supply_v=[4.5,5.5],receiver_vih_min_v=2.,receiver_vil_max_v=.8,
        oscillator_voh_min_v=.9*4.5,oscillator_vol_max_v=.1*5.5,
        high_margin_v=.9*4.5-2.,low_margin_v=.8-.1*5.5,
        receiver_transition_limit_ns_per_v=20,static_threshold_pass=True,
        scope='Static levels at the archived device conditions. Transition compliance remains open.')
    assert dc['high_margin_v']>0 and dc['low_margin_v']>0
    result=dict(passed=True,scope='Static interface and nominal footprint only',dc=dc,
        footprint=dict(source=str(source),sha256=digest,pads=pads,manufacturer_nominal_pitch_mm=[7.62,7.62],
            manufacturer_pitch_tolerance_mm=.2,lead_nominal_diameter_mm=.46,lead_max_diameter_mm=None,
            body_max_mm=[12.7,12.7,5.6],nominal_pin_grid_matches=True,full_insertion_tolerance_qualified=False),
        waveform=dict(duty_percent_at_half_supply=[45,55],rise_fall_max_ns=10,
            rise_fall_measurement_levels='not stated in the archived two-page sheet',
            receiver_threshold_duty_guaranteed=False,monotonicity_qualified=False,
            cycle_jitter_max_ns=None,receiver_slew_qualified=False,
            digital_sensitivity_duties_percent=[37,45,50,55,63],
            sensitivity_rationale='37/63 expands 45/55 by 8 percentage points (20 ns at nominal 250 ns). This is an assumed stress range, not a manufacturer-derived bound.'),
        startup=dict(manufacturer_startup_max_ms=10,external_reset_fixture_hold_after_valid_supply_ms=25,
            nominal_fixture_surplus_ms=15,physical_reset_qualified=False,
            note='The digital tests exercise ideal reset edges and staged release. They do not model power ramps, shallow brownouts, oscillator startup waveforms or metastability.'),
        manufacturer_revision='2016-11-15; current lifecycle/latest revision and procurement remain unverified',
        physical_qualification=False)
    (HERE/'interface.json').write_text(json.dumps(result,indent=2)+'\n')
    folder=HERE/'schematic-svg';folder.mkdir(exist_ok=True)
    run=subprocess.run(['kicad-cli','sch','export','svg','--output',str(folder),str(HERE/'native/Counted-Clock.kicad_sch')],capture_output=True,text=True)
    (HERE/'schematic-svg.log').write_text(run.stdout+run.stderr)
    assert run.returncode==0,run.stdout+run.stderr
    assert (folder/'Counted-Clock.svg').exists()
    print('Static margins: high 2.05 V, low 0.25 V; nominal 7.62 mm pin grid matches; dynamic/assembly qualification open')


if __name__=='__main__':main()
