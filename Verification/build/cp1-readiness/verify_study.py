"""Audit retained experiments independently of simulation success/failure."""
import collections
import json
import re
from frequency_sweep import HERE,ROOT,sha,write

def main():
    lock=json.loads((ROOT/'Verification/targets/cp1/lock.json').read_text())
    rows=[];checked=0
    for tree in ('sweep','sweep-capture'):
        for receipt in sorted((HERE/tree).glob('*/result.json')):
            r=json.loads(receipt.read_text());folder=receipt.parent
            for key,h in r['input_hashes'].items():
                assert lock['artifacts'][key]==h
                assert sha(HERE.parent/key)==h
                if not key.endswith('/tb.sv'):assert sha(folder/key.split('/')[-1])==h
                checked+=1
            for name,h in r['output_hashes'].items():
                assert sha(folder/name)==h,(folder,name)
                checked+=1
            source=next(HERE.parent/key for key in r['input_hashes'] if key.endswith('/tb.sv'))
            original=source.read_text();bench=(folder/'tb.sv').read_text()
            # Verify every original fatal assertion verbatim, with multiplicity.
            pattern=r'\$fatal\([^;]+;'
            assert collections.Counter(re.findall(pattern,original))==collections.Counter(re.findall(pattern,bench))
            log=(folder/'simulation.log').read_text()
            marker='DONE fetched-opcodes cases=454 cycles=23002' if r['cases'] else 'DONE sequencer cycles=1424 halts=3 stepped=12'
            assert r['passed']==(r['exit_code']==0 and marker in log)
            assert r['passed'] or (r['exit_code']!=0 and 'FATAL:' in log),'Incomplete experiment'
            rows.append(dict(tree=tree,label=r['label'],passed=r['passed'],mhz=r['oscillator_mhz'],
                corner=r['corner'],duty=r['duty'],cases=r['cases'],ppm=r['ppm'],
                receipt=str(receipt.relative_to(HERE)),sha256=sha(receipt)))
    for tree,corners,count,aggregate in (('sweep',(0,1,4,7),37,'frequency-results.json'),
                                        ('sweep-capture',(1,4,7),28,'capture-results.json')):
        short=[r for r in rows if r['tree']==tree and not r['cases']]
        assert len(short)==count
        expected={(4,1,.5,0)}|{(f,c,d,30) for f in (5,6,8) for c in corners for d in (.37,.5,.63)}
        assert {(r['mhz'],r['corner'],r['duty'],r['ppm']) for r in short}==expected
        assert next(r for r in short if r['mhz']==4)['passed']
        saved=json.loads((HERE/aggregate).read_text())
        assert saved['completed'] and not saved['physical_qualification']
        for r in saved['runs']:
            assert r==json.loads((HERE/tree/r['label']/'result.json').read_text())
    opcode=[r for r in rows if r['cases']]
    assert len(opcode)==1 and opcode[0]['passed'] and opcode[0]['mhz']==5
    traces=[]
    for receipt in sorted((HERE/'trace').glob('*/result.json')):
        r=json.loads(receipt.read_text())
        assert sha(HERE/r['parent']/'result.json')==r['parent_receipt_sha256']
        for name,h in r['hashes'].items():assert sha(receipt.parent/name)==h;checked+=1
        traces.append(str(receipt.relative_to(HERE)))
    assert len(traces)==3
    screen=json.loads((HERE/'timing-screen.json').read_text())
    for key,h in screen['input_hashes'].items():assert sha(HERE.parent/key)==h==lock['artifacts'][key]
    for row in screen['rows']:
        p=next(p for p in screen['paths'] if p['id']==row['path'])
        assert row['required_ns']==sum(p['terms'].values())
        assert abs(row['margin_ns']-(row['available_ns']-row['required_ns']))<1e-9
    write(HERE/'study-validation.json',dict(passed=True,physical_qualification=False,
        source_and_output_hash_checks=checked,experiments=len(rows),passes=sum(r['passed'] for r in rows),
        retained_failures=sum(not r['passed'] for r in rows),rows=rows,traces=traces,
        analytical_rows=len(screen['rows']),timing_screen_sha256=sha(HERE/'timing-screen.json'),
        recommendation=dict(oscillator_hz=4000000,microcycle_hz=500000,status='conditional engineering target'),
        scope='Evidence integrity and unchanged assertions. Simulation failures are expected study outcomes.'))
    print(f'Validated {len(rows)} experiments, {len(traces)} traces, {len(screen["rows"])} analytical rows; {checked} hashes.')

if __name__=='__main__':main()
