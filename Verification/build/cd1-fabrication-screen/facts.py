"""Source-backed process facts; numerical selections are not supplier bounds."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
SOURCES = HERE/'sources'


def row(file, label):
    rows = json.loads((SOURCES/(file+'.tables.json')).read_text())
    return next(r for r in rows if r[0] == label)


def main():
    facts = []
    def add(name, value, kind, source, evidence, note=''):
        facts.append(dict(name=name, value=value, kind=kind, source=source, evidence=evidence, note=note))
    for name, label, value in [
        ('clearance_mm','Minimum Clearance',.1524), ('track_width_mm','Minimum track Width',.1524),
        ('connection_width_mm','Minimum Connection Width',.1524), ('annulus_mm','Minimum Annular Ring',.127),
        ('via_diameter_mm','Minimum Via Diameter',.508), ('hole_clearance_mm','Copper to hole clearance',.127),
        ('drill_mm','Minimum Through Hole',.254), ('hole_to_hole_mm','Hole to hole clearance',.127),
        ('silk_text_thickness_mm','Silkscreen Min Text Thickness',.127)]:
        add(name,value,'published design minimum','oshpark-rules.html',row('oshpark-rules',label))
    for name, label, value, kind in [
        ('copper_edge_mm','Board Edge Keepout',.381,'published design minimum'),
        ('mask_web_mm','Minimum soldermask web',.1016,'published process minimum'),
        ('mask_alignment_mm','Maximum soldermask alignment',.0762,'published process maximum'),
        ('board_thickness_mm','Board Thickness',1.6,'nominal'),
        ('substrate_er_10mhz','Dielectric',4.5,'service value; no tolerance stated'),
        ('hole_position_service_mm','Drill Positional Tolerance',.0508,'published maximum; conflicts with drill page')]:
        add(name,value,kind,'oshpark-two-layer.html',row('oshpark-two-layer',label))
    tables=json.loads((SOURCES/'oshpark-two-layer.tables.json').read_text())
    for name,label,value,tolerance in [('core_mm','core',1.524,.1524),
                                      ('copper_mm','1 oz copper',.03556,None),
                                      ('mask_mm','solder resist',.01524,.00508)]:
        evidence=next(r for r in tables if len(r)>1 and r[1]==label)
        add(name,dict(nominal=value,plus_minus=tolerance),'nominal stackup and published tolerance',
            'oshpark-two-layer.html',evidence,'Converted from mil using exactly 0.0254 mm/mil; rounded metric display retained in evidence.')
    for name,label in [('hole_size_mm','Fabricated Hole Size Tolerance'),
                       ('hole_position_drill_page_mm','Fabricated Hole Position Tolerance')]:
        add(name,.0635,'published +/- maximum','oshpark-drills.html',row('oshpark-drills',label))
    rules=(SOURCES/'oshpark-rules.txt').read_text()
    mask=next(line for line in rules.splitlines() if line.startswith('Solder Mask Expansion should'))
    add('mask_expansion_mm',.0508,'recommendation','oshpark-rules.html',mask)
    drill=(SOURCES/'oshpark-drills.txt').read_text()
    ring=next(line for line in drill.splitlines() if line.startswith('The annular ring spec accounts'))
    add('annulus_tolerance_already_accounted',True,'supplier interpretation','oshpark-drills.html',ring,
        'Compare nominal CAD annulus directly with 0.127 mm. Do not subtract process tolerances and reapply this minimum.')
    add('laminate_er',dict(typical_1mhz=4.8,typical_1ghz=4.6,specification_maximum=5.4),
        'material datasheet; typical values for reference','kingboard-kb6167f.pdf',
        'Page 1, electrical properties: IPC-4101E/126; Dk <=5.4; typical 4.8 (1 MHz), 4.6 (1 GHz).',
        'Not a broadband finished-board permittivity bound.')
    add('mask_er',4.5,'material test result; applicability unresolved','taiyo-psr4000bn.pdf',
        'Page 6: internal test at 1 MHz, dielectric constant 4.5. Page 1: Green or Dark Green; revised March 2005.',
        'The service is purple. Linked green-mask data does not qualify the delivered purple coating.')
    result=dict(candidate_supplier='OSH Park two-layer prototype',facts=facts,
        selected_hole_position_screen_mm=.0635,
        selection_reason='Use the larger published value for local sensitivity; source discrepancy remains unresolved.',
        unresolved=['Hole-position specification conflict: 0.0508 vs +/-0.0635 mm.',
                    'Finished copper tolerance and exact coating formulation/profile are unstated.',
                    'Material dielectric tests use different frequencies and do not bound edge-rate behavior.',
                    'Actual component lead sizes, sockets, connectors and assembly fit remain unqualified.',
                    'KiCad supplier guide names 9.x; local KiCad is 10.0.8. Offline CAM parsing is not supplier acceptance.'],
        supplier_selected=False,uploaded=False,ordered=False,fabrication_ready=False)
    (HERE/'supplier-facts.json').write_text(json.dumps(result,indent=2)+'\n')
    print(len(facts),'sourced facts; drill-position conflict retained')


if __name__=='__main__':main()
