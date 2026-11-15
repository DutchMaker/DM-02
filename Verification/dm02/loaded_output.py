"""Normal PILOT-03 stage: rerun manufacturer-model evidence, never import a pass."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from .common import BUILD, ROOT, VROOT, digest, evidence, write_json
from . import ibis_driver
from .analog_acceptance import evaluate


def require_private(path):
    # Staged source trees can themselves live below the served Verification
    # root. Resolve symlinks and reject every enclosing served tree.
    served=[p for p in (VROOT,*VROOT.parents) if p.name=='Verification']
    if any(Path(path).resolve().is_relative_to(p.resolve()) for p in served):
        raise ValueError('Model cache and derived circuits must be outside the served Verification directory')
    return Path(path).resolve()


def cache_directory():
    cache=Path(os.environ.get('DM02_MODEL_CACHE',str(Path.home()/'.cache/dm02/models'))).expanduser().resolve()
    return require_private(cache)


def input_hashes():
    paths=[VROOT/'analog-contract.json',VROOT/'requirements.json',VROOT/'models.json',
           VROOT/'vendor/controller/sn74hct574.txt']
    paths.extend(VROOT/'dm02'/name for name in ('loaded_output.py','ibis_driver.py','ibis_factors.py',
        'ibis_transient.py','analog_acceptance.py'))
    return {str(p.relative_to(ROOT)):digest(p) for p in paths}


def run():
    folder=BUILD/'analog/loaded';folder.mkdir(parents=True,exist_ok=True)
    cache=cache_directory()
    missing=[name for name in ('sclm097a.ibs','ibischk7_64') if not (cache/name).is_file()]
    if missing:
        write_json(folder/'state.json',dict(state='blocked',missing=missing))
        return evidence('analog','Bounded manufacturer-model loaded output','blocked',
            'Private model/checker cache missing; run Verification/prepare_analog.py. No cached acceptance was reused.',
            missing=missing,artifacts=['analog/loaded/state.json'])
    for name in ('sclm097a.ibs','ibischk7_64'):
        require_private(cache/name)
    # Optional scientific packages are needed only once the licensed input
    # cache is present. An import/solver failure is a harness error, not a pass.
    from .ibis_transient import experiment
    before=input_hashes()
    write_json(folder/'state.json',dict(state='running',source_hashes=before))
    contract=json.loads((VROOT/'analog-contract.json').read_text())
    requirements=json.loads((VROOT/'requirements.json').read_text())
    models=json.loads((VROOT/'models.json').read_text())['models']
    assert next(m for m in models if m['id']=='hct245')['candidate_mpn']==contract['part']=='SN74HCT245N'
    assert next(m for m in models if m['id']=='hct574')['candidate_mpn']=='SN74HCT574N'
    receiver=(VROOT/'vendor/controller/sn74hct574.txt').read_text()
    assert re.search(r'VIH\s+High-level input voltage.*\s2\s+',receiver)
    assert re.search(r'VIL\s+Low-level input voltage.*0\.8',receiver)
    assert re.search(r'Ci\s+4\.5 V to 5\.5 V\s+3\s+10',receiver)
    # Each invocation has private scratch space, so a failed simulator cannot
    # inherit output files from an earlier successful call or concurrent run.
    with tempfile.TemporaryDirectory(prefix='run-',dir=cache) as scratch:
        private=Path(scratch)
        try:
            text,driver=ibis_driver.qualify(cache/'sclm097a.ibs',cache/'ibischk7_64',private,folder)
            write_json(folder/'driver.json',driver)
            with (folder/'simulation.log').open('w') as log,contextlib.redirect_stdout(log):
                data=experiment(text,contract,private,folder)
            write_json(folder/'experiment.json',data)
            checked=evaluate(contract,data,requirements)
            assert input_hashes()==before,'Analogue inputs changed during execution'
            assert digest(cache/'sclm097a.ibs')==ibis_driver.MODEL_HASH,'Model changed during execution'
            assert hashlib.sha1((cache/'ibischk7_64').read_bytes()).hexdigest()==ibis_driver.CHECKER_SHA1,'Checker changed during execution'
        except Exception as error:
            write_json(folder/'state.json',dict(state='error',error=str(error),source_hashes=before))
            raise
    write_json(folder/'contract.json',contract)
    write_json(folder/'acceptance.json',dict(requirement='PILOT-03',requirement_status='pass',
        scope=contract['scope'],checks=checked,source_hashes=before,
        model_sha256=ibis_driver.MODEL_HASH,physical_clock_qualified=False,
        full_operating_envelope_qualified=False))
    write_json(folder/'state.json',dict(state='complete',source_hashes=before))
    artifacts=[str(p.relative_to(BUILD)) for p in sorted(folder.rglob('*')) if p.is_file()]
    return evidence('analog','Bounded manufacturer-model loaded output','pass',
        f"50 pF / 1 kohm at 5 V / 25 C: both transitions pass; {checked['minimum_setup_margin_ns']:.3f} ns minimum margin; nine faults detected.",
        scope=contract['scope'],checks=checked,artifacts=artifacts,
        limitation='Nominal bounded experiment only. Full PVT, actual PCB/socket loads, OE handover and physical clock/reset remain PILOT-05 gaps.')
