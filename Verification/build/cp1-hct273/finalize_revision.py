"""Accept CP1-R2 only after its full rerun, pin checks and frozen inputs agree."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((HERE/name).read_text())
def main():
    state=read('verification-state.json');assert state['state']=='complete' and state['passed']
    source=read('source-manifest.json')
    for name,h in source['candidate_sources'].items():assert sha(HERE/'candidate'/name)==h,name
    runs=state['runs'];cpu=[x for x in runs if 'cases' in x]
    assert len(cpu)==29 and len([x for x in cpu if x['cases']])==3
    assert sum(bool(x.get('full')) for x in runs)==3
    assert len(read('clock-check.json')['runs'])==150 and read('clock-check.json')['passed']
    for name,count in [('module-check.json',4),('mar-check.json',3),('register-check.json',5)]:
        d=read(name);assert d['passed'] and len(d['runs'])==count and all(x['passed'] for x in d['runs'])
    assert read('fault-check.json')['passed']
    assert read('part-qualification.json')['passed'] and read('part-qualification.json')['missing_hold_monitor_mutation_detected']
    assert read('native-audit.json')['native_passed'] and read('native-audit.json')['structure_passed']
    assert read('interconnect-check.json')['passed'] and read('physical-review.json')['passed']
    assert read('workbook-validation.json')['passed'] and read('rom-check.json')['passed']
    count=0;observations=[]
    for x in runs+read('module-check.json')['runs']+read('mar-check.json')['runs']+read('register-check.json')['runs']:
        assert x['passed']
        log=HERE/x['log'];folder=log.parent
        for name,h in x['model_hashes'].items():assert sha(folder/name)==h,(folder,name);count+=1
        for name,h in x.get('fixture_hashes',{}).items():assert sha(folder/name)==h,(folder,name)
        for name,h in x.get('schematic_hashes',{}).items():assert sha(HERE/'candidate/Circuits/KiCad/Compact/candidates'/f'{name}.sch')==h
        for device,events,minimum in re.findall(r'CP273 hold (\S+) events=(\d+) minimum_ns=([\d.]+)',log.read_text()):
            if int(events):
                assert float(minimum)>=3,(log,device,minimum)
                observations.append(dict(log=x['log'],device=device,events=int(events),minimum_hold_ns=float(minimum)))
    assert count==446 and observations
    boot=next(x for x in cpu if x.get('boot'));assert boot['boot_check']['passed'] and not boot['coverage']['boot_injected']
    assert boot['output']['passed'] and boot['output']['text']=='Hello world\r:-)'
    assert boot['output']['pixels_checked']==48000 and boot['output']['pixel_errors']==0
    assert boot['output']['pixel_sha256']==boot['coverage']['output']['pixel_sha256']
    # Every substituted physical register must actually see post-capture data changes in full boot.
    boot_holds=[x for x in observations if x['log']==boot['log']]
    assert {x['device'].split('.')[-1] for x in boot_holds}=={'U2','U11','U15'}
    folder=(HERE/boot['log']).parent;budget=json.loads((folder/'simulation-budget.json').read_text())
    assert budget['expected_microcycles']==boot['coverage']['microcycles']==2840175
    assert budget['watchdog_ns']==11361700000 and budget['watchdog_ns']>budget['nominal_schedule_ns']
    startup=bytes(int(x,16) for x in (folder/'sram-power-on.hex').read_text().split());assert len(startup)==65536
    write=dict(passed=True,budget=budget,decoded_sram_sha256=hashlib.sha256(startup).hexdigest(),decoded_sram_bytes=len(startup),fresh_full_boot=True)
    (HERE/'program-budget-check.json').write_text(json.dumps(write,indent=2)+'\n')
    image=HERE/'candidate/Verification/build/compact/fixtures-boot/boot-rom.bin'
    assert sha(image)==boot['coverage']['image']['rom_sha256'] and image.stat().st_size==65536
    shutil.copyfile(image,HERE/'programming-images/W27C512-45Z-boot.bin')
    images={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (HERE/'programming-images').glob('*.bin')}
    (HERE/'programming-check.json').write_text(json.dumps(dict(images=images,physical_programming_readback=False,byte_order='Little-endian words for M27C322/M27C1024; byte-addressed W27C512. Programmer/readback remains outstanding.'),indent=2)+'\n')
    receipt_names=('verification-state.json','module-check.json','mar-check.json','register-check.json','clock-check.json','fault-check.json',
        'part-qualification.json','native-audit.json','interconnect-check.json','physical-review.json','component-review.json','rom-check.json','workbook-validation.json','source-manifest.json')
    acceptance=dict(passed=True,revision='CP1-R2',digital_only=True,physical_qualification=False,cpu_profiles=29,
        clock_profiles=150,full_counter_profiles=3,standalone_module_profiles=4,mar_profiles=3,verified_model_artifact_hashes=count,
        selected_273='CD74HCT273E',full_digital_rerun=True,hold_observations=observations,
        minimum_observed_hold_ns=min(x['minimum_hold_ns'] for x in observations),boot_hold_observations=boot_holds,
        specification_gap_closed='The selected 273 now has explicit clock/clear delay limits in SCHS174D; 3 ns hold is monitored in every new simulation.',
        physical_boundary=read('physical-review.json')['open_items'],key_receipt_sha256={n:sha(HERE/n) for n in receipt_names})
    (HERE/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n')
    print('CP1-R2 digital acceptance complete:',count,'model artifacts;',acceptance['minimum_observed_hold_ns'],'ns minimum sampled hold')
if __name__=='__main__':main()
