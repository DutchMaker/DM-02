"""Create a self-contained ACH experiment without changing normal hashed inputs."""
from pathlib import Path
import hashlib
import json
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SANDBOX=HERE/'sandbox'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def replace(text,old,new,count=1):
    assert text.count(old)==count,(old,text.count(old),count)
    return text.replace(old,new)


def main():
    inputs=list((ROOT/'Verification/dm02').glob('*.py'))
    inputs+=list((ROOT/'Verification/vendor/kicad5').glob('*.lib'))
    inputs+=list((ROOT/'Circuits/KiCad/Libraries').glob('*.lib'))
    inputs += [ROOT/p for p in (
        'Verification/designs/clock_candidate.py','Verification/hdl/clock_candidate_tb.sv',
        'Verification/requirements.json','Verification/clock-parts.json',
        'Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch',
        'Verification/build/component-followup/abracon-ach-2016.pdf',
        'Verification/build/component-followup/abracon-ach-2016.txt',
        'Verification/build/component-followup/abracon-ach-source.json',
        'Verification/build/component-followup/ach-review.json',
        'Verification/vendor/clock/sn74ahct04.txt')]
    manifest=[]
    for original in sorted(inputs):
        relative=original.relative_to(ROOT);archive=HERE/'sources'/relative
        archive.parent.mkdir(parents=True,exist_ok=True)
        if archive.exists():assert sha(archive)==sha(original),f'Archived source changed: {relative}'
        else:shutil.copyfile(original,archive)
        dest=SANDBOX/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(archive,dest)
        manifest.append(dict(source=str(relative),sha256=sha(archive)))
    (HERE/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Use the ordinary library resolver inside a separate repository-shaped
    # snapshot. No monkeypatching of global library caches or live modules.
    lib=SANDBOX/'Circuits/KiCad/Libraries/DM02-ACH.lib'
    text=(SANDBOX/'Circuits/KiCad/Libraries/DM02-Clock.lib').read_text()
    text=text.replace('ECS-100AX','ACH-4MHz').replace('1 NC, 7 case/GND, 8 output, 14 VCC','1 NC, 4 case/GND, 5 output, 8 VCC')
    text=replace(text,'X GND 7 ','X GND 4 ')
    text=replace(text,'X OUT 8 ','X OUT 5 ')
    text=replace(text,'X VCC 14 ','X VCC 8 ')
    lib.write_text(text)
    generator=SANDBOX/'Verification/designs/clock_candidate.py';text=generator.read_text()
    text=replace(text,"'DM02-Clock:ECS-100AX','Y1','ECS-100AX-080'","'DM02-ACH:ACH-4MHz','Y1','ACH-4.000MHZ-EK'")
    text=replace(text,"{'1':None,'7':'GND','8':'OSC_TTL','14':'5V'},'Oscillator:Oscillator_DIP-14'",
                      "{'1':None,'4':'GND','5':'OSC_TTL','8':'5V'},'Oscillator:Oscillator_DIP-8'")
    text=text.replace('8 MHz / 8','4 MHz / 8').replace('C1 candidate: 1 MHz full cycle','C1-ACH experiment: 500 kHz full cycle')
    text=replace(text,'Rev "C1"','Rev "C1-ACH-EXPERIMENT"')
    generator.write_text(text)
    parts_path=SANDBOX/'Verification/clock-parts.json';parts=json.loads(parts_path.read_text())
    ach=json.loads((SANDBOX/'Verification/build/component-followup/ach-review.json').read_text())
    osc=parts['oscillator']
    osc.update(mpn=ach['candidate'],frequency_hz=ach['frequency_hz'],stability_ppm=ach['stability_ppm'],
        duty_min=.45,duty_max=.55,startup_max_ms=10,supply_min_v=4.5,supply_max_v=5.5,
        temperature_min_c=-20,temperature_max_c=70,source='abracon-ach-2016',source_pages=[1,2],
        output_pin='5',ground_pin='4',supply_pin='8',nc_pin='1',standard_load_pf=15,
        duty_reference='half supply; NOT an AHCT threshold-crossing guarantee')
    parts['revision']='C1-ACH-isolated'
    parts['unqualified'] += ['ACH edge measurement levels and monotonic threshold crossing are not specified in the archived family sheet.',
        'Nominal 45/55 duty applies at half supply. The 37/63 receiver-duty sweep is a hypothetical sensitivity, not a guaranteed oscillator limit.',
        'ACH standard load is 15 pF, including the 10 pF AHCT04 input and all routing/socket/probe capacitance.']
    parts_path.write_text(json.dumps(parts,indent=2)+'\n')
    model=SANDBOX/'Verification/dm02/clock.py';text=model.read_text()
    text=replace(text,'self.n("Y1",8)','self.n("Y1",self.parts["oscillator"]["output_pin"])')
    model.write_text(text)
    # Parameters express oscillator-relative timing instead of 8 MHz constants.
    tb=SANDBOX/'Verification/hdl/clock_candidate_tb.sv';text=tb.read_text()
    text=replace(text,'real duty=0.5,ppm=0,period,reset_release=-100000;',
        'real duty=0.5,ppm=0,period,reset_release=-100000;\n  parameter real NOMINAL_PERIOD_NS=250.0;')
    text=replace(text,'period=125.0/','period=NOMINAL_PERIOD_NS/')
    text=text.replace('>1500','>12*period').replace('+1500','+12*period')
    text=replace(text,'<468','<4*period-32')
    text=replace(text,'<343','<3*period-32',2)
    text=replace(text,'>407','>3*period+32',2)
    for old,new,count in [('#3000;','#(24*period);',1),('#1500;','#(12*period);',1),
        ('#(2000+i*31)','#(16*period+i*31)',1),('#5000;','#(40*period);',1),
        ('#(1100+i*17)','#(8.8*period+i*17)',1),
        ('#2000000;','#(16000*NOMINAL_PERIOD_NS);',1)]:text=replace(text,old,new,count)
    tb.write_text(text)
    changes=[]
    for row in manifest:
        dest=SANDBOX/row['source']
        if sha(dest)!=row['sha256']:changes.append(dict(file=row['source'],before=row['sha256'],after=sha(dest)))
    changes.append(dict(file=str(lib.relative_to(SANDBOX)),after=sha(lib)))
    (HERE/'adaptations.json').write_text(json.dumps(changes,indent=2)+'\n')
    print('Archived',len(manifest),'inputs; prepared',len(changes),'explicit experiment adaptations')


if __name__=='__main__':main()
