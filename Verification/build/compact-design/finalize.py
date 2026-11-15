"""Accept only the complete, hash-consistent CP1 digital evidence set."""
from pathlib import Path
import hashlib,json,shutil,importlib.util
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(name):return json.loads((HERE/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    state=read('verification-state.json');assert state['state']=='complete' and state['passed']
    modules=read('module-check.json');assert modules['passed'] and modules['complete'] and len(modules['runs'])==4
    mar=read('mar-check.json');assert mar['passed'] and mar['complete'] and len(mar['runs'])==3
    runs=state['runs'];cpu=[x for x in runs if 'cases' in x]
    assert len(cpu)==29 and sum(bool(x['cases']) for x in cpu)==3
    assert sum(x.get('full',False) for x in runs)==3
    assert all(x['passed'] for x in runs+modules['runs'])
    model_count=0
    for x in runs+modules['runs']+mar['runs']+read('register-check.json')['runs']:
        folder=(HERE/x['log']).parent
        for name,h in x['model_hashes'].items():assert sha(folder/name)==h,(folder,name);model_count+=1
        for name,h in x.get('schematic_hashes',{}).items():assert sha(HERE/'candidate/Circuits/KiCad/Compact/candidates'/f'{name}.sch')==h
        for name,h in x.get('fixture_hashes',{}).items():assert sha(folder/name)==h
    boot=next(x for x in cpu if x.get('boot'));assert boot['boot_check']['passed'] and not boot['coverage']['boot_injected']
    budget_check=read('program-budget-check.json');assert budget_check['passed']
    boot_folder=(HERE/boot['log']).parent
    startup=bytes(int(x,16) for x in (boot_folder/'sram-power-on.hex').read_text().split())
    assert len(startup)==65536 and hashlib.sha256(startup).hexdigest()==budget_check['decoded_sram_sha256']
    budget=json.loads((boot_folder/'simulation-budget.json').read_text())
    assert budget['expected_microcycles']==boot['coverage']['microcycles']
    assert budget['watchdog_ns']>budget['nominal_schedule_ns']
    assert boot['output']['passed'] and boot['output']['pixels_checked']==48000 and boot['output']['pixel_errors']==0
    assert boot['output']['pixel_sha256']==boot['coverage']['output']['pixel_sha256']
    assert boot['output']['text']=='Hello world\r:-)'
    assert len(read('clock-check.json')['runs'])==150 and read('clock-check.json')['passed']
    assert read('fault-check.json')['passed'] and read('register-check.json')['passed']
    assert read('native-audit.json')['native_passed'] and read('interconnect-check.json')['passed']
    assert read('physical-review.json')['passed'] and read('component-review.json')['remaining_compatible_273_pairs']==0
    baseline=read('baseline-sources.json')
    for name,h in baseline.items():assert sha(ROOT/name)==h,('Normal source changed',name)
    image_folder=HERE/'programming-images'
    boot_image=HERE/'candidate/Verification/build/compact/fixtures-boot/boot-rom.bin'
    assert sha(boot_image)==boot['coverage']['image']['rom_sha256']
    assert boot_image.stat().st_size==65536
    shutil.copyfile(boot_image,image_folder/'W27C512-45Z-boot.bin')
    program=dict(images={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in image_folder.glob('*.bin')},
        boot_payload=boot['coverage']['image'],physical_programming_readback=False,
        byte_order='M27C322/M27C1024 are little-endian 16-bit words in ascending word-address order. W27C512 is byte-addressed. Verify the programmer/adapter convention with readback.')
    (HERE/'programming-check.json').write_text(json.dumps(program,indent=2)+'\n')
    result=dict(passed=True,digital_only=True,cpu_profiles=len(cpu),full_counter_profiles=3,standalone_module_profiles=4,
        mar_profiles=3,verified_model_artifact_hashes=model_count,clock_profiles=150,normal_inputs_unchanged=len(baseline),
        physical_qualification=False,physical_boundary=read('physical-review.json')['open_items'],
        acceptance_scope='All CP1 digital acceptance suites completed. Existing physical and independent-review requirements remain open; no normal-run error was overwritten.',
        key_receipt_sha256={name:sha(HERE/name) for name in ('verification-state.json','module-check.json','mar-check.json','native-audit.json','interconnect-check.json','physical-review.json','component-review.json','rom-check.json','clock-check.json','fault-check.json','register-check.json','workbook-validation.json')})
    (HERE/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
