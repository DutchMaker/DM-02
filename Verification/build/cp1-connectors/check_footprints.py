"""Bounded footprint/catalog screen; mounting-side drawings visually transcribed.

Manufacturer catalog PDF pages 48-51 (printed 01.20-01.23). Numeric grid and
hole screening does not establish assembly orientation, coding or mating fit.
"""
from pathlib import Path
import json
import math
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.sexpr import parse
from dm02.common import digest,write_json

URL='https://b2b.harting.com/files/livebooks/en/PRD0200000100063/downloads/livebook.pdf'
LIB=Path.home()/'Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Connector_DIN.pretty'
SPECS={
    'male':dict(part='09031966921',footprint='DIN41612_C_3x32_Male_Horizontal_THT',
        table_pdf_page=48,drawing_pdf_page=49,mount_spacing_mm=88.9,
        body_length_max_mm=94.0,contact_axis=0,row_axis=1,mount_row_offset_mm=-2.54),
    'female':dict(part='09032966824',footprint='DIN41612_C_3x32_Female_Vertical_THT',
        table_pdf_page=50,drawing_pdf_page=51,mount_spacing_mm=90.0,
        body_length_max_mm=95.0,contact_axis=1,row_axis=0,mount_row_offset_mm=2.24),
}


def main():
    assert not (HERE/'manifest.json').exists(),'Preserve published study; use a new revision directory'
    catalog=HERE/'sources/harting-din-catalog.pdf'
    assert digest(catalog)=='46280e3eedb9f76a61cbcc40c5bdff2652cb20bd4a89161bde1d3f630865fb41','Catalog source changed'
    records={}
    for role,spec in SPECS.items():
        source=LIB/(spec['footprint']+'.kicad_mod')
        dest=HERE/'sources'/source.name
        if not dest.exists():shutil.copyfile(source,dest)
        pads=[x for x in parse(dest.read_text()) if isinstance(x,list) and x and x[0]=='pad']
        contact={p[1]:p for p in pads if p[1]}
        mounts=[p for p in pads if not p[1]]
        assert len(contact)==96 and len(mounts)==2
        xy=lambda p:[float(v) for v in next(x for x in p if isinstance(x,list) and x[0]=='at')[1:3]]
        drill=lambda p:float(next(x for x in p if isinstance(x,list) and x[0]=='drill')[1])
        checked=0
        for row in 'abc':
            for n in range(1,33):
                p=contact[f'{row}{n}'];point=xy(p)
                assert p[2]=='thru_hole' and math.isclose(drill(p),1.0,abs_tol=1e-6)
                assert math.isclose(point[spec['contact_axis']],(n-1)*2.54,abs_tol=1e-6)
                assert math.isclose(point[spec['row_axis']],'abc'.index(row)*2.54,abs_tol=1e-6)
                checked+=1
        assert math.isclose(math.dist(xy(mounts[0]),xy(mounts[1])),spec['mount_spacing_mm'],abs_tol=1e-6)
        for p in mounts:
            assert p[2]=='np_thru_hole' and 2.8<=drill(p)<=2.9
            assert math.isclose(xy(p)[spec['row_axis']],spec['mount_row_offset_mm'],abs_tol=1e-6)
        # The drawing's 1.0 +/-0.1 and 2.8 +0.1 dimensions still need a
        # finished-hole fabrication tolerance, not just nominal CAD values.
        records[role]=dict(**spec,sha256=digest(dest),contacts_checked=checked,
            signal_hole_nominal_mm=1.0,signal_hole_drawing_range_mm=[0.9,1.1],
            mounting_hole_nominal_mm=drill(mounts[0]),mounting_hole_drawing_range_mm=[2.8,2.9],
            numbered_grid_nominal_match=True,mounting_spacing_nominal_match=True,
            mounting_centres=[xy(p) for p in mounts])
    result=dict(passed=True,physical_qualification=False,footprint_release=False,
        manufacturer_catalog=dict(url=URL,sha256=digest(catalog),bytes=catalog.stat().st_size,
            consulted_pdf_pages=[48,49,50,51],transcription='Visual reading of manufacturer Type C drawings and exact part tables'),
        candidates=records,
        remaining_owners={'current_drawing_and_mate_confirmation':'dm02-57n.2.3',
            'mating_transform_keying_support_and_stack_height':'dm02-57n.6.3',
            'finished_hole_tolerances_and_DFM':'dm02-57n.6.3'},
        scope='96 contact grid coordinates and drill nominals per candidate, mounting-hole spacing/offset and catalog body-length screen. No 3D assembly or physical fit acceptance.')
    write_json(HERE/'footprint-screen.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
