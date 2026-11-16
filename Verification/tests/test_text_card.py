from pathlib import Path
import json
import tempfile
import unittest
from dm02 import text_card,text_cpu,text_evidence


class TextCardTests(unittest.TestCase):
    def test_native_evidence_replays_all_bytes_mutations_and_cpu(self):
        _,matrix,audit=text_evidence.load()
        self.assertEqual(sum(r['passed'] for r in matrix['standalone'].values()),6)
        self.assertEqual(sum(r['passed'] for r in matrix['cpu'].values()),6)
        self.assertEqual(audit['dip_count'],37)
        self.assertEqual(audit['over_screen'],[])
        self.assertEqual(len(audit['connector_bindings']),96)

    def test_missing_sources_or_negative_artifacts_are_rejected(self):
        for key,name in [('source_hashes','Verification/hdl/text_tb.sv'),
                         ('artifacts','cp1-text/final/fault-mailbox-overwrite/simulation.log')]:
            lock=json.loads(text_evidence.LOCK.read_text());del lock[key][name]
            with self.assertRaisesRegex(ValueError,'Missing TX1'):text_evidence.verify(lock)

    def test_diagnostic_bounded_polling_in_architectural_interpreter(self):
        from dm02.control import State,instruction
        from dm02.microcode import reference
        spec=reference((text_cpu.ROOT/'Code/Microcode/microcode.src').read_text())['instructions']
        class Endpoint(State):
            def get(self,address):
                if address==0xff03:
                    self.polls+=1
                    return (0x80 if self.polls%3 else 0x81) if self.reply is None else self.reply
                if address==0xff10:return self.marker
                return super().get(address)
            def put(self,address,value):
                if address==0xff00:self.transcript.append(value)
                elif address==0xff10:self.marker=value
                else:super().put(address,value)
        for reply in (None,0,0x80,0x83):
            with self.subTest(reply=reply):
                state=Endpoint(pc=0);state.memory=dict(enumerate(text_cpu.diagnostic()))
                state.transcript=[];state.polls=0;state.marker=0;state.reply=reply
                for _ in range(10000):
                    op=state.get(state.pc);state.pc+=1
                    instruction(spec[op]['name'],spec[op]['size'],state)
                    if state.halted:break
                self.assertTrue(state.halted)
                self.assertEqual(state.marker,0x5a if reply is None else 0xee)
                self.assertEqual(bytes(state.transcript),text_cpu.TRANSCRIPT if reply is None else b'')
                if reply==0x80:self.assertEqual(state.polls,255)

    def test_native_pin_supply_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            original=text_card.STUDY/'iteration-2/native/TX1/TX1.xml'
            # Move an actual VCC pin into an unrelated net in the XML.
            import xml.etree.ElementTree as ET
            tree=ET.parse(original);nets=tree.findall('./nets/net')
            supply=next(n for n in nets if n.get('name')=='/5V')
            pin=next(p for p in supply.findall('node') if p.get('ref')=='U1' and p.get('pin')=='20')
            supply.remove(pin);next(n for n in nets if n.get('name')=='/GND').append(pin)
            tree.write(root/'TX1.xml')
            with self.assertRaisesRegex(ValueError,'supply pins'):text_card.Circuit(root)

    def test_prior_run_is_preserved(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'Preserve prior'):text_card.simulate(None,Path(name))


if __name__=='__main__':unittest.main()
