"""OS1 reproducible native audit, waveform analysis and measurement contract."""
import json
from .common import ROOT,VROOT,BUILD,digest,write_json
from . import oscillator_interface as oi,oscillator_waveforms as waves,mar_distribution_evidence as mde

LOCK=VROOT/'oscillator-evidence.json'
SOURCES=['Verification/oscillator-interface.json','Verification/operating-contract.json',
    'Verification/dm02/oscillator_interface.py','Verification/dm02/oscillator_waveforms.py',
    'Verification/dm02/oscillator_evidence.py','Verification/mar-distribution-evidence.json']
require=oi.require


def measurement_plan(audit):
    oc=json.loads((VROOT/'operating-contract.json').read_text())
    return dict(contract=oc['revision'],status='specification; unmeasured',physical_qualification=False,
        supply_points_v=oc['qualification_matrix']['supply_points_v'],ambient_points_c=oc['qualification_matrix']['ambient_points_c'],
        links=[dict(name=f['name'],pins=[p['id'] for p in f['raw']['pins']],
            conditioned_outputs=[r['driver'] for r in f['conditioned']],
            actual_raw_capacitance_pf=None,measured_input_edge_ns=None,receiver_threshold_duty=None,
            jitter_ns=None,startup_ns=None,qualified_delay_ns=None) for f in audit['frontends']],
        procedure=[
            'Confirm exact ACH-4.000MHZ-EK markings and first-receiver DIP identities. Pin 1 is NC for this suffix, not a reset or enable input. Keep both oscillators running through HALT; do not derive CPU clock from the text card.',
            'Bound receiver input capacitance over actual voltage/temperature, each fitted socket, trace/via/pad and probe attachment. Raw-clock design targets: 10 pF conditional IC subtotal + 2 pF sockets + 1 pF route + 1 pF probe = 14 pF, leaving 1 pF against 15 pF rating. No full-envelope bound is inferred. Qualify the particular low-capacitance probe; a 10 pF passive probe exceeds this budget.',
            'Measure both raw outputs and every listed conditioned output at the receiver pins. Validate the local conditioned-link targets, including CPU CLK_P 40 pF IC subtotal with 8 pF parasitic target and 2 pF planning margin. Extract actual routes; no route length follows without stack/geometry.',
            'Ask manufacturer to define ACH rise/fall reference levels and jitter/load conditions. Record 10-90%, 0.8-to-2 V, 1.5 V crossings and Vdd/2 separately. Check monotonic edges, overshoot, undershoot and repeated crossings. The CPU AHCT04 <=3 ns and TEXT HCT244 6 ns timing-generator conditions differ from recommended input-transition limits.',
            'Measure first-stage propagation and rise/fall asymmetry at actual load and input slew, plus conditioned edges at subsequent receivers. For CPU measure CLK_P/CLK_N separation and INIT_CLK; for TEXT measure OSC_CLK before counters and request synchronizer. Do not infer a full-chain timing guarantee from the presence of a buffer.',
            'At all nine OC1 supply/temperature points capture period, cycle-to-cycle/period jitter, high/low widths and duty at both half supply and receiver references. Include uncertainty and drift; test the receiver-duty 0.37..0.63 and 2 ns routing/jitter allocations only as design targets, not manufacturer specifications.',
            'Capture slow/interrupted supply ramps and clock startup, then reset/stop/resume/step/HALT. Reset release requires a qualified clock and a restartable 25 ms continuously valid-supply guard; the oscillator 10 ms startup maximum alone cannot authorize reset release.',
            'Record instrument/probe identities and calibration, measured load, threshold/skew uncertainty, exact parts/lots, waveform files and sample/repetition coverage. Reviewer must approve any sample-qualified envelope and design guard; nine grid points do not establish population or continuous-envelope guarantees.'
        ],issues=['dm02-57n.3.6','dm02-57n.4.2.2','dm02-57n.8.1','dm02-57n.8.2','dm02-57n.7.2'],
        records=oc['qualification_matrix']['measurement_record'],review_required=True)


def summary(build=BUILD):
    inventory=json.loads((build/'cp1-mar-distribution/final/loads.json').read_text())
    native=oi.audit(inventory)
    return dict(revision='CP1-OS1',native=native,mutations=oi.faults(inventory),waveforms=waves.matrix(),
        measurement_plan=measurement_plan(native),physical_qualification=False,hardware_changed=False,promoted_into_R2=False,
        source_review=dict(ahct04_pdf_sha256='79e359c70a08e3a6a9318beea502f99e101b304f9ff1d4fe205c40c2d9c48c78',
            ahct04_page7_visual='Figure 6-1 note C: PRR <=1 MHz, ZO=50 ohms, tr<=3 ns and tf<=3 ns; input reference 1.5 V, output reference VCC/2. Figure was not extracted by pypdf from the full PDF; visually reviewed extracted page retained.',
            abracon='2016 sheet:15 pF,10 ns at4MHz,45/55 atVdd/2,10ms startup;no specified jitter or tr/tf voltage levels.',
            hct244='SCHS167G section5.9:CL50pF,input tr/tf6ns. HCT data propagation31ns and output transition15ns at4.5V/-40..85C. No claim that15ns output meets downstream6ns timing fixtures.'))


def verify(lock,build=BUILD):
    require(lock.get('revision')=='CP1-OS1' and lock.get('physical_qualification') is False,'Invalid OS1 evidence scope')
    require(set(SOURCES)<=lock['source_hashes'].keys(),'Missing OS1 source')
    required={'cp1-oscillator/summary.json','cp1-oscillator/sources/sn74ahct04-full.pdf',
              'cp1-oscillator/sources/sn74ahct04-waveform.pdf','cp1-oscillator/sources/sn74ahct04-full.txt',
              'cp1-oscillator/sources/retrieval.json','cp1-link-loads/sources/abracon-ach-2016.txt',
              'cp1-link-loads/sources/cd74hct244.txt'}
    require(required<=lock['artifacts'].keys(),'Missing OS1 artifact')
    for root,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            path=(root/name).resolve();require(path.is_relative_to(root.resolve()),'OS1 path escape')
            require(path.is_file() and digest(path)==sha,'Changed OS1 evidence: '+name)
    mde.load(build);actual=summary(build)
    require(actual==json.loads((build/'cp1-oscillator/summary.json').read_text()),'OS1 analysis replay differs')
    require(digest(build/'cp1-oscillator/sources/sn74ahct04-full.pdf')==actual['source_review']['ahct04_pdf_sha256'],'AHCT04 source revision changed')
    return actual


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());return lock,verify(lock,build)
