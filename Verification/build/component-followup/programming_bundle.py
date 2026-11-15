"""Prepare labelled binary images and compare operator-supplied chip readbacks.

This utility never communicates with a programmer. It retains the completed
normal report and connected boot snapshot as the origins of each image.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
BUILD=HERE.parent
BASELINE=BUILD/'experiments/2026-11-15-normal-complete'
CONNECTED=BUILD/'experiments/2026-11-15-connected'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(destination):
    report=json.loads((BASELINE/'report.json').read_text())
    checks={c['id']:c for c in report['checks']}
    assert report['state']=='complete' and checks['alu']['status']==checks['microcode']['status']=='pass'
    assert checks['flash-array']['status']==checks['alu-flash']['status']=='limited'
    manifest=json.loads((CONNECTED/'manifest.json').read_text())
    def baseline(path):
        source=BASELINE/path;assert sha(source)==report['artifact_hashes'][path],path;return source
    def connected(path):
        source=CONNECTED/path;assert sha(source)==manifest['files'][path]['sha256'],path;return source
    destination.mkdir(parents=True,exist_ok=True);devices=[]
    def image(source,file,board,ref,mpn,role):
        target=destination/file;shutil.copyfile(source,target);assert sha(target)==sha(source)
        devices.append(dict(file=file,board=board,reference=ref,mpn=mpn,role=role,bytes=target.stat().st_size,
                            sha256=sha(target),source=str(source.relative_to(BUILD))))
    original=b''.join(baseline(f'alu/alu{i}.rom').read_bytes() for i in range(8))
    assert len(original)==4194304
    for bank in range(4):
        for lane in range(2):
            label='high' if lane else 'low';ref=f'U{101+bank*2+lane}'
            source=baseline(f'alu-flash/images/bank{bank}-{label}.bin')
            assert source.read_bytes()==original[bank*1048576+lane:(bank+1)*1048576:2]
            image(source,f'AL2-{ref}-bank{bank}-{label}.bin','AL2 (AL1 connector slot)',ref,'SST39SF040-70-4I-NHE',f'ALU bank {bank}, {label} byte')
    microcode=baseline('microcode/microcode.rom').read_bytes();assert len(microcode)==131072
    for lane,label in enumerate(('low','high')):
        file=f'CW1-U{lane+1}-{label}.bin';path=destination/file;path.write_bytes(microcode[lane::2])
        devices.append(dict(file=file,board='CW1',reference=f'U{lane+1}',mpn='AT27C512R-70PU',role=f'Control word {label} byte',
                            bytes=path.stat().st_size,sha256=sha(path),source='experiments/2026-11-15-normal-complete/microcode/microcode.rom'))
    image(connected('bootloader-graphics-fixture/boot-rom.bin'),'ME1-U1-boot.bin','ME1','U1','AT27C512R-70PU','BL1 boot ROM; lower 16 KiB decoded')
    assert len(devices)==11 and all(r['bytes']==(524288 if r['board'].startswith('AL2') else 65536) for r in devices)
    result=dict(schema_version=1,devices=devices,normal_report_sha256=sha(BASELINE/'report.json'),
                connected_manifest_sha256=sha(CONNECTED/'manifest.json'),
                scope='Prepared logical images only. Physical programming/readback and programmer/adapter suitability remain unverified. '
                      'Use the labelled per-device files; the simulation alu.bin and the combined 16-bit microcode.rom are not per-chip images. '
                      'Compare a full-device readback captured after programming, using the identical file name in a separate directory.')
    (destination/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');return result


def compare_readbacks(bundle,readbacks):
    manifest=json.loads((bundle/'manifest.json').read_text());rows=[]
    for device in manifest['devices']:
        file=device['file'];expected=bundle/file;actual=readbacks/file
        if sha(expected)!=device['sha256']:raise ValueError('Prepared image changed: '+file)
        if not actual.is_file():rows.append(dict(file=file,passed=False,error='missing readback'));continue
        got=actual.read_bytes();want=expected.read_bytes()
        differences=[i for i,(a,b) in enumerate(zip(got,want)) if a!=b]
        rows.append(dict(file=file,passed=got==want,expected_bytes=len(want),read_bytes=len(got),sha256=hashlib.sha256(got).hexdigest(),
                         mismatched_bytes=len(differences)+abs(len(got)-len(want)),first_mismatch_offsets=differences[:16]))
    return dict(passed=all(r['passed'] for r in rows),devices=rows,
                scope='Byte comparison of operator-supplied files only. The tool cannot establish that files came from physical chips.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('bundle',type=Path);parser.add_argument('--readbacks',type=Path)
    args=parser.parse_args();result=compare_readbacks(args.bundle,args.readbacks) if args.readbacks else prepare(args.bundle)
    print(json.dumps(result,indent=2))
    if args.readbacks and not result['passed']:raise SystemExit(1)
