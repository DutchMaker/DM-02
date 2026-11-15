"""Compare footprint-only repairs to the preserved complete-run sources."""
import json
import shutil
from dm02.common import ROOT,BUILD,digest,write_json
from dm02.legacy import read_sheet,connectivity
from dm02.native_migrate import validate
from dm02.distribution_hardware import load_boards,exported_hdl
from dm02.controller_hardware import Circuit as Word
from dm02.alu_hardware import Circuit as Alu
from dm02.alu_flash import Circuit as Flash
from designs.distribution_candidate import SOURCE

folder=BUILD/'assembly-repaired'
archive=BUILD/'experiments/2026-11-15-integrated-complete/sources'
changes=json.loads((folder/'changes.json').read_text());native=[]
for row in changes['changed']:
    source=ROOT/row['source'];dest=folder/'native'/source.stem
    assert digest(source)==row['after_sha256']
    assert connectivity(read_sheet(source))==connectivity(read_sheet(archive/row['source']))
    cached=dest/'comparison.json'
    result=json.loads(cached.read_text()) if cached.exists() else None
    if not result or result['source_hash']!=digest(source):result=validate(read_sheet(source),dest)
    assert result['status']=='pass',result
    native.append(dict(source=row['source'],result=result))
    print(source.stem,'native pass',flush=True)
standalone=[('CW1',Word,'Circuits/KiCad/Controller/candidates/Control-Word.sch'),
            ('AL1',Alu,'Circuits/KiCad/ALU/candidates/Timed-ALU.sch'),
            ('AL2',Flash,'Circuits/KiCad/ALU/candidates/Flash-ALU.sch')]
hdl=[]
for name,cls,path in standalone:
    before=cls(read_sheet(archive/path));after=cls(read_sheet(ROOT/path))
    for corner in range(5):
        assert before.hdl(corner)==after.hdl(corner),(name,corner)
        hdl.append(dict(board=name,corner=corner,identical=True))
before=load_boards(archive/SOURCE.relative_to(ROOT));after=load_boards(SOURCE)
for name in after:
    for corner in range(5):
        assert exported_hdl(before[name],corner,name)==exported_hdl(after[name],corner,name),(name,corner)
        hdl.append(dict(board='FD1/'+name,corner=corner,identical=True))
write_json(folder/'validation.json',dict(passed=True,native=native,hdl=hdl,
    scope='Native KiCad validates all seven changed sheets. Standalone and FD1 HDL equal the archived source-derived HDL at all five logic corners.'))
shutil.copyfile(BUILD/'assembly-preflight/inventory.py',folder/'inventory.py')
print(len(native),'native checks and',len(hdl),'exact HDL comparisons passed',flush=True)
