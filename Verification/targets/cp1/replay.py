#!/usr/bin/env python3
"""Regenerate accepted CP1 models in an isolated source root, then smoke-test."""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main(workspace, archive, receipt):
    def read(name):
        return json.loads((archive/name).read_text())
    def load(name):
        path = workspace/(name+'.py')
        shutil.copyfile(archive/path.name, path)
        spec = importlib.util.spec_from_file_location('cp1_'+name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    r = load('run')
    from dm02.common import ROOT, VROOT, BUILD, digest
    from dm02.compact_hardware import Circuit, support_hdl
    from designs.compact_candidate import generate
    from dm02.boot_hardware import memory_hdl, testbench
    require(ROOT == workspace/'candidate', 'Wrong CP1 import root')
    expected_sources = read('source-manifest.json')['candidate_sources']
    generate()
    generated = []
    for name, expected in expected_sources.items():
        require(digest(ROOT/name)==expected, 'Regeneration changed source: '+name)
        if name.startswith('Circuits/KiCad/Compact/'):
            generated.append(name)
    fixture = BUILD/'compact/fixtures'
    fixture.mkdir(parents=True, exist_ok=True)
    for path in (archive/'candidate/Verification/build/compact/fixtures').iterdir():
        if path.is_file():
            shutil.copyfile(path, fixture/path.name)
    runs = read('verification-state.json')['runs']
    require(read('verification-state.json')['state']=='complete', 'Incomplete acceptance')
    require(all(x['passed'] for x in runs), 'Failed profile')
    cpu = [x for x in runs if 'cases' in x]
    require(len(cpu)==29 and sum(bool(x['cases']) for x in cpu)==3, 'Missing CPU profiles')
    require(sum(bool(x.get('full')) for x in runs)==3, 'Missing exhaustive counter profiles')
    count = 0
    def compare(result, texts):
        nonlocal count
        require(set(texts)==set(result['model_hashes']), 'Changed model file set: '+result['log'])
        for name,text in texts.items():
            require(sha(text)==result['model_hashes'][name], 'Model mismatch: '+result['log']+' / '+name)
            count += 1
    for x in cpu:
        texts = {n+'.sv':Circuit(n).hdl(x['corner']) for n in
                 ('C1','CW1','SQ1','PC1','AL1','RG1','SP1','MA1','ME1','BF1','DT1')}
        texts['support.sv'] = (VROOT/'hdl/controller_devices.sv').read_text()+support_hdl()
        texts['tb.sv'] = r.bench()
        if x.get('boot'):
            texts['ME1.sv'] = memory_hdl(texts['ME1.sv'])
            texts['support.sv'] = texts['support.sv'].replace(
                'initial $readmemh("program.hex",memory,0,65535);',
                'initial $readmemh("sram-power-on.hex",memory);')
            texts['tb.sv'] = testbench(texts['tb.sv'],x['coverage']).replace(
                'DEMO ? 4000000000.0',f'DEMO ? {r.program_watchdog(x["coverage"],x["ppm"])["watchdog_ns"]:.3f}')
            require(x['boot_check']['passed'] and not x['coverage']['boot_injected'], 'Host-injected boot')
            require(x['output']['pixels_checked']==48000 and x['output']['pixel_errors']==0, 'Boot output mismatch')
        compare(x,texts)

    # Exercise the original preparation code, stopping before compilation.
    # No simulator output or passing simulation status is fabricated.
    class Prepared(Exception):
        pass
    def stop_before_compile(args, **kwargs):
        require(args[0]=='iverilog', 'Unexpected preparation command')
        raise Prepared()
    groups = [('counters',[x for x in runs if 'full' in x],lambda x:(x['corner'],x['full'],x['fault'])),
              ('registers',read('register-check.json')['runs'],lambda x:(x['corner'],x['fault'])),
              ('module_checks',read('module-check.json')['runs'],lambda x:(x['board'],x['corner'],x['quick'])),
              ('mar_checks',read('mar-check.json')['runs'],lambda x:(x['corner'],x['full'],x['fault']))]
    for name, profiles, arguments in groups:
        module = load(name)
        module.command = stop_before_compile
        for x in profiles:
            require(x['passed'], 'Failed standalone profile')
            try:
                module.run(*arguments(x))
            except Prepared:
                pass
            else:
                raise ValueError('Preparation did not reach compiler')
            folder = (workspace/x['log']).parent
            compare(x,{p.name:p.read_text() for p in folder.glob('*.sv')})
    clocks = read('clock-check.json')['runs']
    require(len(clocks)==150 and all(x['passed'] for x in clocks), 'Clock profile gap')
    for corner in range(10):
        expected = archive/f'candidate/Verification/build/compact/clock-c{corner}/clock.sv'
        require(sha('`define DM02_OSC_PERIOD_NS 250\n'+Circuit('C1').hdl(corner))==digest(expected), 'Clock model mismatch')
    require(count==read('acceptance.json')['verified_model_artifact_hashes'], 'Incomplete model equivalence')
    # A fresh short integration run also checks simulator/tool compatibility.
    smoke = r.profile(corner=1)
    require(smoke['passed'], 'Fresh CP1 integration smoke failed')
    smoke_path = workspace/smoke['log']
    shutil.copyfile(smoke_path,receipt.parent/'smoke.log')
    result = dict(passed=True,model_hashes_compared=count,clock_models_compared=10,
                  regenerated_sources=generated,source_files_checked=len(expected_sources),
                  fresh_smoke=dict(passed=True,corner=1,log='cp1/smoke.log',wall_seconds=smoke['wall_seconds']),
                  full_simulations='Reused pinned accepted evidence; full boot not rerun.')
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main(*(Path(p).resolve() for p in sys.argv[1:]))
