from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from dm02.common import ROOT
from dm02.legacy import read_sheet,library
from dm02.native_migrate import validate,blocks,flatten


class NativeMigration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='dm02-native-')
        self.addCleanup(self.temp.cleanup);self.folder=Path(self.temp.name)

    def fixture(self):
        source=read_sheet(ROOT/'Circuits/KiCad/Power-Clock/Power-Clock.sch')
        supervisor=next(c for c in source['components'] if c['ref']=='U5')
        candidate=read_sheet(ROOT/'Circuits/KiCad/Power-Clock/candidates/Counted-Clock.sch')
        connector=next(c for c in candidate['components'] if c['ref']=='J1')
        sheet=dict(name='Transforms',source=source['source'],components=[],wires=[],labels=[],
                   junctions=[],no_connects=[],buses=[],bus_entries=[])
        matrices=[(1,0,0,-1),(1,0,0,1),(-1,0,0,-1),(-1,0,0,1),
                  (0,1,1,0),(0,1,-1,0),(0,-1,1,0),(0,-1,-1,0)]
        for i,m in enumerate(matrices):
            for original,ref,x,y in [(supervisor,f'U{i+1}',1500+i*1500,1500),
                                      (connector,f'J{i+1}',1500+i*1500,3500)]:
                c=deepcopy(original);c.update(ref=ref,original_ref=ref,x=x,y=y,stamp=f'{ref}-fixture',
                                            matrix=m if ref.startswith('U') else (1,0,0,-1))
                ns,name=c['lib_id'].split(':');a,b,cc,d=c['matrix']
                c['pins']=[dict(p,x=x+a*p['x']+b*p['y'],y=y+cc*p['x']+d*p['y'])
                           for p in library(ns)[name]['pins'] if p['unit'] in (0,1) and p['convert'] in (0,1)]
                for p in c['pins']:
                    if int(p['number'])<=3:
                        sheet['labels'].append(dict(name=f'PAIR{i}_PIN{p["number"]}',x=p['x'],y=p['y'],implicit=False))
                sheet['components'].append(c)
        return sheet

    def test_native_geometry_all_eight_transforms(self):
        r=validate(self.fixture(),self.folder)
        self.assertEqual(r['differences'],[])
        self.assertEqual(r['components'],16)
        self.assertEqual(r['physical_pins'],88)
        self.assertEqual(r['connected_nets'],24)
        self.assertEqual(r['net_groups'],64)

    def test_wrong_python_pin_interpretation_is_detected(self):
        sheet=self.fixture()
        sheet['components'][0]['pins'][0]['number']='99'
        r=validate(sheet,self.folder)
        self.assertEqual(r['status'],'fail')
        self.assertTrue(any(('U1','99') in row['nodes'] for row in r['differences']))

    def test_alias_inheritance_preserves_native_pin_body(self):
        symbols={'Base':'(symbol "Base" (property "Value" "Base") (symbol "Base_1_1" (pin input line (number "1"))))',
                 'Alias':'(symbol "Alias" (extends "Base") (property "Value" "Alias"))'}
        fields=flatten('Alias',symbols)
        self.assertIn('(symbol "Base_1_1" (pin input line (number "1")))',fields)
        self.assertIn('(property "Value" "Alias")',fields)
        self.assertNotIn('(property "Value" "Base")',fields)
        self.assertEqual(blocks('(root (item "quoted ) ("))'),['(item "quoted ) (")'])


if __name__=='__main__': unittest.main()
