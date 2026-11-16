"""Fail-closed promotion of CP1's immutable, completed digital evidence."""
import json
import platform
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from .common import ROOT, VROOT, BUILD, digest, write_json, command, evidence
from .reporting import sources, now, trace, milestones
from . import operating_contract

TARGET = VROOT/'targets/cp1'


def checked_path(root, name):
    path = (root/name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path escapes evidence root: '+name)
    return path


def verify_hashes(root, expected):
    for name, value in expected.items():
        path = checked_path(root, name)
        if not path.is_file() or digest(path) != value:
            raise ValueError('Missing or changed locked input: '+str(path))


def archive_root(lock):
    return checked_path(BUILD,lock.get('evidence_directory','compact-design'))


def materialize(lock, destination):
    """Never import the overlay into the dashboard/reference Python process."""
    for name, expected in lock['sources'].items():
        origin = TARGET/'overlay' if name in lock['overlay'] else ROOT
        source = checked_path(origin, name)
        if not source.is_file() or digest(source) != expected:
            raise ValueError('CP1 source requires new verification: '+str(source))
        target = checked_path(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def validated_evidence(lock, output):
    verify_hashes(BUILD, lock['artifacts'])
    with tempfile.TemporaryDirectory(prefix='cp1-', dir=output) as temporary:
        workspace = Path(temporary)
        materialize(lock, workspace/'candidate')
        code, log = command([sys.executable, TARGET/'replay.py', workspace, archive_root(lock),
                             output/'equivalence.json'], timeout=300)
        (output/'equivalence.log').write_text(log)
        if code:
            raise RuntimeError('CP1 regeneration failed; see cp1/equivalence.log')
    result = json.loads((output/'equivalence.json').read_text())
    if not result.get('passed'):
        raise ValueError('CP1 equivalence did not pass')
    return result


def checks_from_evidence(lock):
    archive = archive_root(lock)
    directory = str(archive.relative_to(BUILD.resolve()))
    def check(id, title, status, summary, *artifacts, **extra):
        return evidence(id, title, status, summary,
                        artifacts=[directory+'/'+p for p in artifacts], **extra)
    checks = [check('cp1-equivalence','CP1 active source and evidence equivalence','pass',
                    'Checked-in CP1 overlay and shared sources reproduce accepted physical-pin HDL. Saved simulations are reused with pinned inputs, models, fixtures and logs.',
                    'acceptance.json','source-manifest.json',provenance='locked replay'),
              check('migration','CP1 native connectivity parity','pass',
                    'All 12 sheets match native KiCad connectivity; 230 backplane net groups match HDL interfaces.', 'native-audit.json','interconnect-check.json'),
              check('packages','CP1 physical package allocation','pass',
                    '192 DIP logic/memory packages; 96 fewer than the 288-package baseline. All footprint pads are through-hole.', 'packages.json','physical-review.json'),
              check('electrical','CP1 structural electrical checks','pass',
                    'No unresolved structural findings in 12 sheets; pin and footprint checks passed.', 'audit.json','physical-review.json'),
              check('bom','Exact parts and sourcing','blocked',
                    'Owned HCT191/245/574 manufacturer/suffix/counts and remaining sourcing decisions are open.', 'candidate-BOM.csv','component-review.json'),
              check('alu','Independent ALU image contract','pass',
                    'All 2,097,152 ALU words independently checked.', 'rom-check.json'),
              check('control','CP1 instruction contract','pass',
                    '227 opcodes / 454 cases / 23,002 cycles at each of three delay profiles; 24 continuous CPU profiles and ROM boot passed.', 'verification-state.json'),
              check('control-programs','CP1 compiled demo execution','pass',
                    'ROM boot reaches HALT in 2,840,175 microcycles with exact text and zero errors across 48,000 pixels; no host bootstrap injection.', 'verification-state.json'),
              check('memory','CP1 memory decode and pin routes','pass',
                    '131,073 reads, 48,897 SRAM writes, 16,384 protected ROM writes and 256 IO writes; mixed-delay checks passed.', 'module-check.json'),
              check('registers','CP1 register capture and release','pass',
                    '2,052 captures, 4,096 transfers and four resets per profile; enable and initialization-clock faults detected.', 'register-check.json'),
              check('alu-circuit','CP1 physical ALU paths','pass',
                    '8,192 vectors, 256 flag loads and 64 C/Z commands; mixed-delay checks passed.', 'module-check.json'),
              check('clock-candidate','CP1 sampled clock profiles','pass',
                    '150 profiles passed at a conditional 4 MHz oscillator / 500 kHz microcycle rate.', 'clock-check.json'),
              check('timing','Worst-case physical timing','blocked',
                    'CP1 digital evidence is conditional. HCT273 clock delay, HCT245 loading/release and SRAM turnaround lack qualified bounds; the stated 1 MHz envelope is not demonstrated.', 'physical-review.json'),
              check('physical-clock','Clock and driver qualification','limited',
                    'Sampled digital duty/frequency corners passed. Startup, loaded edges, reset and full-supply behaviour remain unqualified.', 'physical-review.json'),
              check('module-timing','Complete timed module integration','limited',
                    'Schematic-derived digital integration passed; physical load, clock, reset and SRAM turnaround qualification remain open.', 'acceptance.json'),
              check('system','Complete timed machine','limited',
                    'All opcodes and complete ROM boot passed digitally. Physical programming/readback, supply, clock, reset, routing and external IO remain open.', 'acceptance.json'),
              check('electrical-review','Independent electrical review','blocked','Independent review of the selected components and wiring is outstanding.'),
              check('pcb','PCB fabrication review','blocked','Compact schematics are verified digitally; routed PCB review is outstanding.'),
              check('bench','Hardware calibration','blocked','No measured prototype qualification yet.')]
    specification = directory+'/part-qualification.json'
    if lock.get('revision')=='CP1-R2':
        if specification not in lock['artifacts']:
            raise ValueError('CP1-R2 requires pinned component qualification')
        verify_hashes(BUILD,{specification:lock['artifacts'][specification]})
        part = json.loads((archive/'part-qualification.json').read_text())
        if not part.get('passed') or not part.get('missing_hold_monitor_mutation_detected'):
            raise ValueError('Component qualification did not pass')
        checks.append(check('component-specification','CD74HCT273E specification and pin qualification','pass',
            'Three DIP-20 registers have explicit 38/40 ns clock/clear limits at 4.5 V, -40..85 C and 50 pF. All 60 pins match; the required 3 ns data hold is monitored throughout the fresh digital suite, including full boot. Actual loads and input edges remain unqualified.',
            'part-qualification.json','component-review.json','acceptance.json'))
        next(c for c in checks if c['id']=='timing')['summary'] = (
            'CP1-R2 has documented HCT273 delay limits. Actual loads/edges, HCT245 loading/release and SRAM turnaround remain unqualified; the stated 1 MHz envelope is not demonstrated.')
    # These gates concern the unchanged verification method / compiler / PC
    # oracle. Keep their original scope and their failed parent run visible.
    reference = json.loads(checked_path(BUILD,lock['reference_report']).read_text())
    prefix = str(Path(lock['reference_report']).parent)+'/'
    for id in ('pilot','mutations','analog','microcode','control-flow'):
        original = next(c for c in reference['checks'] if c['id']==id)
        if original['status'] != 'pass':
            raise ValueError('Reference gate did not pass: '+id)
        c = json.loads(json.dumps(original))
        c['title'] += ' (preserved reference evidence)'
        c['provenance'] = dict(report=lock['reference_report'], scope='Unchanged verification method or independent software contract; not CP1 physical qualification.')
        c['artifacts'] = [prefix+p for p in c.get('artifacts',[])]
        for case in c.get('cases',[]):
            if 'waveform' in case:
                case['waveform'] = prefix+case['waveform']
        checks.append(c)
    checks.append(evidence('reference-history','Preserved reference-run failures','limited',
        'The original hardware-programs timeout and dependent boot error remain in the archived report. CP1 is a separate accepted digital design.',
        artifacts=[lock['reference_report']]))
    return checks


def run(args, harness_check):
    output = BUILD/'cp1'
    output.mkdir(parents=True, exist_ok=True)
    requirements = json.loads((VROOT/'requirements.json').read_text())
    report = dict(schema_version=1, target='cp1', mode='locked-evidence-replay',
                  started_at=now(), state='running', source_hashes=sources(), checks=[],
                  requirements=requirements, models=dict(target='CP1',parameters='targets/cp1/overlay/Verification/dm02/compact_hardware.py',
                                                        qualification='Selected by the pinned evidence directory',
                                                        frequency='4 MHz oscillator / 500 kHz microcycles, conditional'),
                  risks=[], tools={'python':platform.python_version()},
                  release=dict(status='blocked',message='CP1 — DIGITAL ACCEPTANCE ONLY; physical qualification and PCB review remain open.'))
    def save():
        report['traceability'] = trace(requirements,report['checks'])
        report['milestones'] = milestones(requirements,report['checks'])
        write_json(BUILD/'report.json',report)
    save()
    try:
        lock = json.loads((TARGET/'lock.json').read_text())
        archive = archive_root(lock)
        directory = str(archive.relative_to(BUILD.resolve()))
        report['revision'] = lock.get('revision','CP1')
        report['models']['qualification'] = 'build/'+directory+'/component-review.json'
        report['models']['target'] = report['revision']
        print('Checking CP1 source, evidence and regenerated HDL equivalence…',flush=True)
        report['equivalence'] = validated_evidence(lock, output)
        report['checks'] = checks_from_evidence(lock)
        report['artifact_hashes'] = dict(lock['artifacts'])
        contract = operating_contract.load()
        if contract['design_revision'] != report['revision']:
            raise ValueError('Operating contract does not match the replayed revision')
        requirements = operating_contract.effective_requirements(requirements, contract)
        report['requirements'] = requirements
        report['operating_contract'] = contract
        qualification = operating_contract.matrix(contract)
        write_json(output/'operating-contract.json', contract)
        write_json(output/'qualification-matrix.json', qualification)
        report['checks'].append(evidence('operating-contract','Selected first-build operating contract','pass',
            f'{contract["revision"]}: {contract["clock"]["oscillator_nominal_hz"]/1e6:g} MHz oscillator / '
            f'{contract["clock"]["microcycle_nominal_hz"]/1e3:g} kHz microcycles; 4.75–5.25 V at IC pins, 0–50 °C ambient.',
            artifacts=['cp1/operating-contract.json','cp1/qualification-matrix.json'],
            limitation='This check validates the selected engineering contract and its provenance. Physical qualification and release gates remain open.'))
        next(c for c in report['checks'] if c['id']=='timing')['summary'] = (
            f'{contract["revision"]} selects {contract["clock"]["microcycle_nominal_hz"]/1e3:g} kHz microcycles. '
            'Actual loads/edges, minimum-delay timing, HCT245 release, SRAM turnaround and the MAR transfer window remain unqualified. '
            'The historical 1 MHz requirement remains preserved; it is now a preferred rate, not a release minimum.')
        # Decision evidence participates in the normal post-test hash recheck.
        for name, expected in contract['evidence'].items():
            if name.startswith('Verification/build/'):
                report['artifact_hashes'][name.removeprefix('Verification/build/')] = expected
        report['provenance'] = dict(release=lock['release'], reference_report=lock['reference_report'],
                                   acceptance=directory+'/acceptance.json', operating_contract=contract['revision'],
                                   historical_requirements='Verification/requirements.json')
        boundaries = json.loads((archive/'physical-review.json').read_text())['open_items']
        report['risks'] = [dict(id=f'CP1-{i+1:02}',title=text,severity='open',
                               action='Requires physical or manufacturer qualification.',evidence='timing') for i,text in enumerate(boundaries)]
    except Exception as err:
        (output/'error.log').write_text(traceback.format_exc())
        report['checks'] = [evidence('cp1-equivalence','CP1 acceptance replay','error',str(err),artifacts=['cp1/error.log'])]
    save()
    if args.browser:
        from . import modules
        try:
            report['checks'].append(modules.browser())
        except Exception as err:
            report['checks'].append(evidence('browser','Browser regression','error',str(err)))
    print('Running harness regression tests…',flush=True)
    report['checks'].append(harness_check())
    if sources() != report['source_hashes']:
        report['checks'].append(evidence('source-change','Inputs changed during verification','error','Run again against stable sources.'))
    # Recheck after tests: changes during replay must never acquire a fresh hash.
    if report.get('artifact_hashes'):
        try:
            verify_hashes(BUILD,report['artifact_hashes'])
        except Exception as err:
            report['checks'].append(evidence('evidence-change','Evidence changed during verification','error',str(err)))
    artifacts = {p for c in report['checks'] for p in c.get('artifacts',[])}
    if report.get('equivalence'):
        artifacts.update('cp1/'+p.name for p in output.glob('equivalence.*'))
        artifacts.add('cp1/smoke.log')
    report.setdefault('artifact_hashes',{})
    for p in sorted(artifacts):
        if not (BUILD/p).is_file():
            report['checks'].append(evidence('missing-'+p,'Missing artifact','error',p))
        elif p not in report['artifact_hashes']:
            report['artifact_hashes'][p] = digest(BUILD/p)
    if any(c['status']=='error' for c in report['checks']):
        for c in report['checks']:
            if c['id']=='control':
                c['requirement_status']='blocked'
    report.update(state='complete',finished_at=now())
    save()
    for m in report['milestones']:
        print(f'Milestone {m["number"]}: {m["summary"]}',flush=True)
    for c in report['checks']:
        if c['status']=='error':
            print(c['summary'],flush=True)
    if any(c['status']=='error' for c in report['checks']):
        return 2
    return 0 if args.allow_design_failures else 1
