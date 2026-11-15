"""Publish completed clean-integration checks with self-contained input hashes."""
from datetime import datetime,timezone
import html
import json
from pathlib import Path
import shutil
from dm02.common import ROOT,BUILD,digest,write_json

HERE=Path(__file__).resolve().parent
DEST=BUILD/'experiments/2026-11-15-integration'


def main():
    read=lambda name:json.loads((HERE/name).read_text())
    native=read('native-summary.json');equivalence=read('equivalence.json');hdl=read('hdl-equivalence.json')
    assert len(native)==13 and all(r['status']=='pass' for r in native)
    assert len(equivalence)==13 and all(r['groups_equal'] and r['labels_equal'] and r['parts_equal'] and not r['findings'] for r in equivalence)
    assert len(hdl)==8 and all(r['hdl_files_equal']==12 and r['fixture_equal'] for r in hdl)
    for row in native:assert digest(HERE/'circuits'/f'{row["sheet"]}.sch')==row['source_hash']
    continuous=read('continuous.json');opcodes=read('opcodes.json');hello=read('hello.json')
    assert len(continuous)==8 and len(opcodes)==3 and hello['output']['passed'] and hello['output']['io_events']==15
    runs=continuous+opcodes+[hello['simulation']]
    for row in runs:
        assert row['passed'] and row['inputs_stable']
        for path,want in row['input_hashes'].items():assert digest(ROOT/path)==want,path
        for name,want in row['generated_hdl_hashes'].items():assert digest(ROOT/row['folder']/name)==want,name
    links=read('links.json');assert links['passed'] and links['scratch_fd1_equivalent'] and len(links['rows'])==324
    bp=read('backplane-summary.json');assert bp['comparison']['passed'] and bp['native']['status']=='pass'
    assert len(bp['mutations'])==4 and all(r['detected'] for r in bp['mutations'])
    for path,want in bp['contract']['source_hashes'].items():assert digest(ROOT/path)==want,path
    assert digest(HERE/'Backplane.sch')==bp['native']['source_hash']
    boot=read('boot-fixture/equivalence.json');assert boot['passed']
    for name,want in boot['files'].items():assert digest(HERE/'boot-fixture'/name)==want,name
    boot_hdl=read('boot-hdl-equivalence.json');assert boot_hdl['passed'] and boot_hdl['exact_marker_mutations_detected']==4
    socket=read('components/socket-research/adam-pinmap-summary.json')
    assert socket['numbered_pad_positions_match'] and socket['pins']==32
    assert socket['installed_footprint']['matches_recommended_hole'] is False
    component=HERE/'components/socket-research'
    assert digest(component/'adam-plcc32-orwin.pdf')==socket['provenance']['sha256']
    assert digest(component/socket['candidate_footprint']['file'])==socket['candidate_footprint']['sha256']
    native_socket=read('components/socket-research/adam-native-export.json');assert native_socket['passed']
    assert digest(component/native_socket['svg'])==native_socket['sha256']
    pcn=read('components/oscillator-research/abracon-ach-pcn4615-source.json')
    assert digest(HERE/'components/oscillator-research/abracon-ach-pcn4615.pdf')==pcn['sha256']
    names=['native-summary.json','equivalence.json','hdl-equivalence.json','continuous.json','opcodes.json','hello.json',
           'links.json','backplane-summary.json','Backplane.sch','boot-hdl-equivalence.json',
           'boot-fixture/equivalence.json','boot-fixture/coverage.json','boot-fixture/image.json','boot-fixture/boot-rom.bin',
           'boot-fixture/loader.lst','distribution-parts.json']
    for pattern in ('*.py','circuits/*.sch','native/*/*.kicad_sch','native/*/comparison.json','native/*/libraries.json',
                    'backplane-native/*.kicad_sch','backplane-native/comparison.json','backplane-native/libraries.json'):
        names.extend(str(p.relative_to(HERE)) for p in HERE.glob(pattern))
    names.extend(str(p.relative_to(HERE)) for p in (HERE/'components').rglob('*') if p.is_file())
    for row in runs:
        folder=ROOT/row['folder']
        names.extend(str(p.relative_to(HERE)) for p in folder.iterdir() if p.suffix in ('.sv','.log') or p.name in ('profile.json','io-observed.txt','text.txt'))
    DEST.mkdir(parents=True,exist_ok=True);manifest=dict(created_at=datetime.now(timezone.utc).isoformat(),files={},
        scope='Completed clean-integration staging checks only. Normal runner integration remains pending. '
              'Both scratch full boot-to-graphics results are published on the connected-machine evidence page. '
              'Conditional 4 MHz simulation and allocated loads; no physical qualification or milestone promotion.')
    for name in sorted(set(names)):
        source=HERE/name;target=DEST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        assert digest(source)==digest(target)
        manifest['files'][name]=dict(sha256=digest(target),bytes=target.stat().st_size)
    cards=[('13 clean-generated sheets',
        f'All {sum(r["net_groups"] for r in native):,} pin groups and {sum(r["physical_pins"] for r in native):,} physical pins agree with native KiCad. '
        'Every group, net label and component also matches the completed scratch FD1 circuits. The normal parser resolves all symbols directly.',
        [('native-summary.json','Native KiCad checks'),('equivalence.json','Circuit equivalence'),('distribution_candidate.py','Deterministic generator')]),
      ('Explicit simulation assembly',
        'Eight continuous profiles, three all-opcode profiles and exact hello pass with the staged runner. All 227 opcodes are covered at zero, '
        'maximum and mixed delays. The runner assembles each board explicitly; its generated HDL and fixture match the tested scratch implementation.',
        [('continuous.json','Eight profiles'),('opcodes.json','All-opcode results'),('hello.json','Hello result'),('hdl-equivalence.json','HDL comparison'),('distribution_run.py','Runner')]),
      ('324 links and the backplane',
        'The clean connector audit matches every scratch FD1 endpoint, driver and input load. Each signal link has one driver and at most 50 pF allocated load. '
        'The BP1 backplane preserves 81 headers, 884 pins and the PC address-enable ground strap; native KiCad and four fault mutations pass.',
        [('links.json','Actual-pin load audit'),('backplane-summary.json','Backplane contract and faults'),('backplane-native/Backplane.kicad_sch','Native backplane')]),
      ('Reproducible ROM loader',
        'The clean BL1 host run executes 83,377 instructions and 558,200 cycles, reconstructs 16,542 bytes and performs exactly 24,326 SRAM writes. '
        'Nine generated files match the completed scratch loader evidence byte for byte. The clean boot fixture and memory HDL also match the completed hardware-prefix fixture.',
        [('boot-fixture/coverage.json','Host loader result'),('boot-fixture/equivalence.json','File comparison'),('boot-hdl-equivalence.json','Boot fixture comparison'),
         ('boot-fixture/boot-rom.bin','64 KiB ROM image'),('boot-fixture/loader.lst','Loader listing')]),
      ('Socket mapping and oscillator evidence',
        'Adam Tech’s revision-C drawing provides all 32 socket pad numbers; they match the existing KiCad positions. '
        'Its recommended 1.10 mm holes differ from the installed 0.80 mm footprint. A separate 1.10 mm-drill candidate passes the numbered-map check '
        'and KiCad SVG export. The drawing was obtained from a third-party mirror; physical fit and current manufacturer confirmation remain open. '
        'Archived Abracon PCN 4615 explicitly includes ACH-4.000MHZ-EK and describes a 2023 internal assembly change. Current lifecycle and electrical qualification remain open.',
        [('components/socket-research/adam-pinmap-summary.json','Numbered socket check'),('components/socket-research/adam-plcc32-orwin.pdf','Socket drawing, rev C'),
         ('components/socket-research/native-svg/PLCC-32_AdamTech_PLCC-32-AT_Candidate.svg','Native footprint preview'),
         ('components/socket-research/DM02-Sockets.pretty/PLCC-32_AdamTech_PLCC-32-AT_Candidate.kicad_mod','Separate candidate footprint'),
         ('components/oscillator-research/abracon-ach-pcn4615.pdf','Oscillator PCN')])]
    sections=[]
    for title,text,links_ in cards:
        nav=' · '.join(f'<a href="{html.escape(path)}">{html.escape(label)}</a>' for path,label in links_)
        sections.append(f'<section><h2>{html.escape(title)}</h2><p>{html.escape(text)}</p><nav>{nav}</nav></section>')
    index='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DM-02 · clean integration evidence</title><style>
:root{color-scheme:dark}body{margin:0;background:#0c1420;color:#e2e8f0;font:16px/1.55 system-ui,sans-serif}main{max-width:1080px;margin:auto;padding:30px 18px}a{color:#8acfff;overflow-wrap:anywhere}h1{line-height:1.2}h2{font-size:1.2rem;margin:0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:18px;margin:24px 0}section{background:#152132;border:1px solid #304156;border-radius:10px;padding:22px;min-width:0}.notice{border-left:4px solid #f5b84c;padding:12px 18px;background:#24251f}nav,footer{font-size:.87rem}.muted{color:#aab7c8}</style>
<main><nav><a href="/">Verification dashboard</a> · <a href="../2026-11-15-connected/">Connected-machine evidence</a></nav>
<h1>Clean integration evidence</h1><p class="muted">Captured '''+html.escape(manifest['created_at'])+'''</p>
<p class="notice">Staged under Verification/build while the normal verification run holds its source inputs fixed. Normal runner integration is pending. Both scratch full boot-to-graphics runs have passed; see the connected-machine evidence page. Physical qualification remains open.</p>
<div class="grid">'''+''.join(sections)+'''</div><footer><a href="manifest.json">Artifact hashes</a><p>4 MHz remains a conditional target; the connected interval review rejects 8 MHz. Exact oscillator/reset, SRAM turnaround, programming/readback and PCB work remain open.</p></footer></main></html>'''
    (DEST/'index.html').write_text(index);manifest['files']['index.html']=dict(sha256=digest(DEST/'index.html'),bytes=(DEST/'index.html').stat().st_size)
    write_json(DEST/'manifest.json',manifest)
    print(json.dumps(dict(path=str(DEST),files=len(manifest['files']),created_at=manifest['created_at']),indent=2))


if __name__=='__main__':main()
