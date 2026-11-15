from pathlib import Path
import shutil
import tempfile
import unittest
from dm02.hardware_programs import fixtures,simulate,render


class HardwarePrograms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='dm02-hardware-demo-');cls.folder=Path(cls.temp.name)
        cls.coverage=fixtures(cls.folder/'fixtures','hello_world')

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_hello_world_from_reset_to_external_connector(self):
        for corner in (1,2):
            dest=self.folder/f'valid{corner}';r=simulate(dest,self.folder/'fixtures',corner)
            self.assertTrue(r['passed'],r['log']);output=render(dest,'hello_world')
            self.assertTrue(output['passed']);self.assertEqual(output['io_events'],self.coverage['io_events'])
            self.assertEqual(self.coverage['microcycles'],825)

    def test_wrong_extra_and_missing_io_events_fail(self):
        original=(self.folder/'fixtures/io-expected.txt').read_text().splitlines()
        for name,lines,message in [('wrong',['00 ff']+original[1:],'demo IO event'),
                                   ('unexpected',original[:-1],'demo IO event'),
                                   ('missing',original+['00 00'],'demo missing IO events')]:
            with self.subTest(name=name):
                fixture=self.folder/name;shutil.copytree(self.folder/'fixtures',fixture)
                (fixture/'io-expected.txt').write_text('\n'.join(lines)+'\n')
                r=simulate(self.folder/(name+'-run'),fixture)
                self.assertFalse(r['passed']);self.assertIn(message,r['log'])


if __name__=='__main__':unittest.main()
