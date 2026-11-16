#!/usr/bin/env python3
"""Run evidence collection. Exit 1 means known design gaps; exit 2 means tool/harness errors."""
import argparse
import json
import platform
import re
import subprocess
import sys
import traceback
from dm02 import baseline, pilot, analog, alu, modules, encoding, microcode, control, logisim_pc, programs
from dm02 import packages, electrical, memory, alu_circuit, alu_sequences, clock, reset, pc_hardware, controller_hardware, sequencer, alu_hardware, register_hardware, address_hardware, memory_hardware, hardware_programs, flash_hardware, alu_flash
from dm02.common import BUILD, VROOT, command, evidence, write_json
from dm02.reporting import sources, now, trace, milestones
from dm02 import distribution,distribution_backplane,boot

INTEGRATION_PREREQUISITES={
    'distribution':('alu-flash','memory-hardware','controller-hardware','sequencer-hardware','clock-candidate'),
    'backplane':('distribution',),
    'boot':('distribution','backplane','hardware-programs','alu','microcode'),
}


def integration_prerequisites(name,completed,checks):
    by_id={c['id']:c for c in checks}
    for dependency in INTEGRATION_PREREQUISITES.get(name,()):
        if dependency not in completed or by_id.get(dependency,{}).get('status') not in ('pass','limited'):
            raise RuntimeError(name+' requires successful '+dependency+' evidence from this run')


def harness_check(timeout=600):
    """Keep a bounded regression failure in the report, including partial logs."""
    try:
        code,log=command([sys.executable,'-m','unittest','discover','-s',VROOT/'tests','-v'],
                         cwd=VROOT,timeout=timeout)
    except subprocess.TimeoutExpired as err:
        output=err.stdout or ''
        log=output.decode('utf-8',errors='replace') if isinstance(output,bytes) else output
        log+=f'\nRegression suite timed out after {timeout} seconds.\n'
        code=124
    except OSError as err:
        code=127;log=f'Cannot launch regression suite: {err}\n'
    (BUILD/'tests.log').write_text(log)
    test_count=re.search(r'Ran (\d+) tests?',log)
    tests_ok=code==0 and test_count is not None and int(test_count[1])>0
    return evidence('harness','Verification harness regression tests','pass' if tests_ok else 'error',
                    f'{test_count[1] if test_count else "Unknown number of"} tests executed; '+
                    ('all passed.' if tests_ok else 'suite failed or did not complete; see tests.log.'),
                     exit_code=code,timeout_seconds=timeout,artifacts=['tests.log'])


def link_control_contract(checks):
    """MOD-03 is functional semantics; MOD-08 retains electrical integration."""
    by_id={c['id']:c for c in checks}
    control_check=by_id.get('control');hardware=by_id.get('alu-hardware',{})
    if (not control_check or control_check['status']!='limited' or
            not hardware.get('functional_contract_passed') or hardware.get('status')!='limited' or
            by_id.get('harness',{}).get('status')!='pass' or any(c['status']=='error' for c in checks)):
        return
    control_check['requirement_status']='pass'
    control_check['contract_validation']={
        'evidence':'alu-hardware',
        'semantics':'C1 PH3 capture; CW1 PH1 control latch; AL1 PH1 result isolation and synchronous PH3 flags; pre-increment MAR transfer.',
        'coverage':'227 fetched target opcodes, two flag profiles; all 16 packed flags in continuous branch tests; independent instruction oracle and pin/timing mutations.',
        'boundary':'Functional MOD-03 accepted. Host MAR/stack/register/memory/IO and unqualified electrical loads remain MOD-08/SYS-01 gaps.'}
    control_check['artifacts'].append('alu-hardware/summary.json')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-design-failures',action='store_true',help='Exit 0 after a complete run with known design gaps, but never suppress tool/harness errors')
    parser.add_argument('--browser',action='store_true',help='Also run the real-browser demo regression (requires Playwright and Chrome)')
    args=parser.parse_args()
    BUILD.mkdir(parents=True,exist_ok=True)
    requirements=json.loads((VROOT/'requirements.json').read_text())
    report=dict(schema_version=1,started_at=now(),state='running',source_hashes=sources(),checks=[],
                requirements=requirements,models=json.loads((VROOT/'models.json').read_text()),
                risks=json.loads((VROOT/'risks.json').read_text()),tools={'python':platform.python_version()},
                release=dict(status='blocked',message='NOT READY FOR FABRICATION — partial virtual evidence; no bench qualification.'))
    def save():
        report['traceability']=trace(requirements,report['checks'])
        report['milestones']=milestones(requirements,report['checks'])
        write_json(BUILD/'report.json',report)
    save()
    for tool,args_ in [('kicad',['kicad-cli','version']),('iverilog',['iverilog','-V']),('ngspice',['ngspice','--version']),('node',['node','--version'])]:
        try:
            code,text=command(args_)
            report['tools'][tool]=dict(exit_code=code,output=text[:2000])
        except OSError as err: report['tools'][tool]=dict(error=str(err))
    # Separate stages: a broken tool cannot erase successful independent evidence.
    sheets={}
    stages=[('baseline',lambda:baseline.run()),('packages',packages.run),('electrical',electrical.run),
            ('memory',memory.run),('reset-circuit',reset.run),('clock-candidate',clock.run),('pilot',pilot.run),('analog',analog.run),
              ('encoding',encoding.run),('alu',alu.run),('flash-array',flash_hardware.run),('alu-circuit',alu_circuit.run),('microcode',microcode.run),
               ('pc-circuit',logisim_pc.run),('control',control.run),('pc-hardware',pc_hardware.run),('controller-hardware',controller_hardware.run),('sequencer-hardware',sequencer.run),('alu-hardware',alu_hardware.run),('register-hardware',register_hardware.run),('address-hardware',address_hardware.run),('memory-hardware',memory_hardware.run),('hardware-programs',hardware_programs.run),('alu-flash',alu_flash.run),('alu-sequences',alu_sequences.run),('control-programs',programs.run),('emulator',modules.emulator),
            ('registers',lambda:modules.registers(sheets['Registers-StackPointer']))]
    stages.extend([('distribution',distribution.run),('backplane',distribution_backplane.run),('boot',boot.run)])
    if args.browser: stages.append(('browser',modules.browser))
    completed=set()
    for name,func in stages:
        print(f'Running {name}…',flush=True)
        try:
            integration_prerequisites(name,completed,report['checks'])
            if name in ('alu-circuit','flash-array') and ('alu' not in completed or next(c for c in report['checks'] if c['id']=='alu')['status']!='pass'):
                raise RuntimeError('ALU circuit execution requires passing ROM evidence from this run')
            if name=='pc-hardware' and (not {'alu','microcode','pc-circuit','control','clock-candidate'}<=completed or
                    any(c['status'] not in ('pass','limited') for c in report['checks'] if c['id'] in ('alu','microcode','pc-circuit','control','clock-candidate'))):
                raise RuntimeError('PC replay requires successful ALU, microcode, reference PC, control and C1 evidence from this run')
            if name=='controller-hardware' and ('pc-hardware' not in completed or
                    next(c for c in report['checks'] if c['id']=='pc-hardware')['status'] not in ('pass','limited')):
                raise RuntimeError('Controller execution requires successful PC candidate evidence from this run')
            if name=='sequencer-hardware' and ('controller-hardware' not in completed or
                    next(c for c in report['checks'] if c['id']=='controller-hardware')['status'] not in ('pass','limited')):
                raise RuntimeError('Sequencer execution requires successful control-word evidence from this run')
            if name=='alu-hardware' and ('sequencer-hardware' not in completed or
                    next(c for c in report['checks'] if c['id']=='sequencer-hardware')['status'] not in ('pass','limited')):
                raise RuntimeError('AL1 integration requires successful fetched-sequencer evidence from this run')
            if name=='register-hardware' and ('alu-hardware' not in completed or
                    next(c for c in report['checks'] if c['id']=='alu-hardware')['status'] not in ('pass','limited')):
                raise RuntimeError('RG1 integration requires successful fetched-ALU evidence from this run')
            for stage,dependency in [('address-hardware','register-hardware'),('memory-hardware','address-hardware'),('hardware-programs','memory-hardware'),('alu-flash','memory-hardware'),('alu-flash','flash-array')]:
                if name==stage and (dependency not in completed or
                        next(c for c in report['checks'] if c['id']==dependency)['status'] not in ('pass','limited')):
                    raise RuntimeError(stage+' requires successful '+dependency+' evidence from this run')
            if name=='alu-sequences' and (not {'alu-circuit','microcode','control','pc-circuit'}<=completed or
                    any(c['status'] not in ('pass','limited') for c in report['checks'] if c['id'] in ('alu-circuit','microcode','control','pc-circuit'))):
                raise RuntimeError('ALU sequences require successful circuit, microcode, control and PC evidence from this run')
            if name in ('control','control-programs') and not {'alu','microcode','pc-circuit'}<=completed:
                raise RuntimeError('Control execution requires ALU, microcode and PC circuit evidence from this run')
            if name=='control-programs' and ('memory' not in completed or next(c for c in report['checks'] if c['id']=='memory')['status']!='pass'):
                raise RuntimeError('Program execution requires passing memory-decoder evidence from this run')
            result=func()
            if name=='baseline': result,sheets=result
            report['checks'].extend(result if isinstance(result,list) else [result])
            completed.add(name)
        except Exception as err:
            (BUILD/(name+'-error.log')).write_text(traceback.format_exc())
            report['checks'].append(evidence(name,name+' execution','error',str(err),artifacts=[name+'-error.log']))
        save()
    report['checks'] += [evidence('electrical-review','Independent electrical review','blocked','Package and connectivity checks are automated; independent review of the completed circuit and exact selected parts is outstanding.'),
                            evidence('module-timing','Timed module integration','blocked','See distribution for FD1: AL2 with CD1/RD1/DF2 private links at a conditional 4 MHz target. Allocated link loads and sampled timing remain bounded; SRAM turnaround, oscillator/reset and physical routing qualification keep MOD-08 open.'),
                            evidence('system','Complete timed machine','blocked','See distribution, backplane and boot for FD1/BP1/BL1 evidence from this run. BL1 starts from ROM with poisoned SRAM; physical programming/readback, supply/reset, oscillator, private SRAM turnaround, PCB routing and display electronics remain open.'),
                         evidence('bench','Hardware calibration','blocked','No measured board or prototype results exist in this workflow.')]
    print('Running harness regression tests…',flush=True)
    report['checks'].append(harness_check())
    end_sources=sources()
    if end_sources!=report['source_hashes']:
        report['checks'].append(evidence('source-change','Inputs changed during verification','error','Run again against stable sources.'))
    report['finished_at']=now(); report['state']='complete'
    # Hash artifacts so saved results can be checked for missing/altered evidence.
    artifacts={p for c in report['checks'] for p in c.get('artifacts',[])}
    missing=sorted(p for p in artifacts if not (BUILD/p).is_file())
    if missing:
        report['checks'].append(evidence('missing-artifacts','Missing declared evidence','error',', '.join(missing)))
    # Include detailed stage outputs, not unrelated historical/ad-hoc files in
    # build/. In particular, a later dashboard smoke test has its own result.
    for directory in ('inventory','schematics','native-schematics','pilot','analog','alu','registers','microcode','memory','clock','reset','pc-hardware','controller','sequencer','alu-hardware','register-hardware','address-hardware','memory-hardware','hardware-programs','flash-array','alu-flash','distribution','backplane','boot'):
        artifacts.update(str(p.relative_to(BUILD)) for p in (BUILD/directory).rglob('*')
                         if p.is_file() and p.suffix in ('.vcd','.log','.json','.csv','.sv','.cir','.dat','.xml','.kicad_sch','.kicad_sym','.sch','.rom','.img','.hex','.bin','.txt','.lst','.pgm'))
    report['artifact_hashes']={p:digest_file(BUILD/p) for p in sorted(artifacts) if (BUILD/p).is_file()}
    link_control_contract(report['checks'])
    save()
    for c in report['checks']: print(f'{c["status"]:7} {c["title"]}: {c["summary"].splitlines()[0]}')
    print(f'Report: {BUILD/"report.json"}')
    if any(c['status']=='error' for c in report['checks']): return 2
    return 0 if args.allow_design_failures else 1


def digest_file(path):
    from dm02.common import digest
    return digest(path)


if __name__=='__main__':
    sys.exit(main())
