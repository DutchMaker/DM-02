"""Stage exact footprint-name replacements while normal sources stay frozen."""
from pathlib import Path
import shutil
from dm02.common import ROOT,digest,write_json
from dm02.legacy import read_sheet,connectivity
from dm02.native_migrate import validate
from dm02.sexpr import parse
from dm02.distribution_links import all_boards
from designs.distribution_candidate import SOURCE

HERE=Path(__file__).resolve().parent
LIBRARY=Path.home()/'Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
REPAIRS={
    'Package_SO:SOIC-24_7.5x15.4mm_P1.27mm':'Package_SO:SOIC-24W_7.5x15.4mm_P1.27mm',
    'Package_SO:SOIC-20_7.5x12.8mm_P1.27mm':'Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm',
}


def main():
    rows=[];definitions={}
    for old,new in REPAIRS.items():
        library,part=new.split(':');path=LIBRARY/(library+'.pretty')/(part+'.kicad_mod')
        tree=parse(path.read_text());numbers=sorted({p[1] for p in tree if isinstance(p,list) and p and p[0]=='pad' and p[1]})
        target=HERE/'footprints'/(library+'.pretty')/path.name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
        definitions[old]=dict(replacement=new,numbered_pads=numbers,sha256=digest(path),archived=str(target.relative_to(HERE)))
    final_sources={ROOT/c.sheet['source'] for c in all_boards(SOURCE).values()}
    for source in sorted(final_sources):
        text=source.read_text()
        if not any(old in text for old in REPAIRS):continue
        before=read_sheet(source);dest=HERE/'staged-circuits'/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
        for old,new in REPAIRS.items():text=text.replace('"'+old+'"','"'+new+'"')
        dest.write_text(text);after=read_sheet(dest)
        assert connectivity(before)==connectivity(after),source
        changed=[]
        for a,b in zip(before['components'],after['components'],strict=True):
            want=dict(a,footprint=REPAIRS.get(a['footprint'],a['footprint']))
            assert b==want,(a['ref'],a,b)
            if a['footprint']!=b['footprint']:
                definition=definitions[a['footprint']]
                assert sorted({p['number'] for p in a['pins']})==definition['numbered_pads']
                changed.append(dict(reference=a['ref'],value=a['value'],old=a['footprint'],new=b['footprint']))
        native=validate(after,HERE/'native'/source.stem)
        assert native['status']=='pass',native
        rows.append(dict(source=str(source.relative_to(ROOT)),source_sha256=digest(source),
                         staged=str(dest.relative_to(HERE)),staged_sha256=digest(dest),changes=changed,
                         connectivity_identical=True,native=native))
    result=dict(scope='Staged footprint-name repair only. Source sheets and generators require a later change after the current run is archived. '
                      'Installed footprint pad numbering and native KiCad nets checked; manufacturer package geometry remains a separate qualification.',
                generator_edits=['Verification/designs/controller_candidate.py','Verification/designs/alu_candidate.py'],
                regenerate='Regenerate affected standalone AL1/AL2/CW1 candidates and downstream FD1 sheets after editing generators; retain prior completed run first.',
                definitions=definitions,sheets=rows,changed_physical_references=sum(len(r['changes']) for r in rows),
                passed=len(rows)==2 and sum(len(r['changes']) for r in rows)==6)
    write_json(HERE/'staged-repairs.json',result)
    assert result['passed'];print('Six footprint names repaired in two staged sheets; native KiCad and unchanged net groups pass.')


if __name__=='__main__':main()
