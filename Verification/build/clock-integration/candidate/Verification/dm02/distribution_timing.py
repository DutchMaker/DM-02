"""DF2 conservative delivery/hold intervals under the current microcode.

This adds the fabric to existing ME1 timing derivations. It is not a complete
machine timing certificate: global control/address loads and physical slew,
external IO input stability, reset abort and SRAM turnaround remain open.
"""
import json
import struct
from copy import deepcopy
from .distribution_hardware import Selector,Fabric
from dm02.clock import Clock,budget as clock_budget
from dm02.memory_hardware import Circuit as Memory,budget as memory_budget
from dm02.controller_hardware import Circuit as Controller
from dm02.sequencer import Circuit as Sequencer
from dm02.common import BUILD,digest
from . import controller_hardware,sequencer,alu_flash,register_hardware,address_hardware,memory_hardware


def source_change_risks(words):
    risks=[];triples={};data_words=0
    for address,word in enumerate(words):
        if not word&0x8000:continue
        data_words+=1;source=(word>>11)&15;load=(word>>7)&15;function=0 if word&64 else (word>>1)&15
        triple=(source,load,function);triples[triple]=triples.get(triple,0)+1;reason=None
        if source in range(1,6) and load==source:reason='source register is also loaded; needs an explicit self-copy hold proof'
        elif source==7 and (load==7 or function in (9,10,11,12)):reason='packed flags can change at receiver capture'
        elif source in (8,9) and (load in (8,9) or function in (6,7,8)):reason='visible MAR can change at receiver capture'
        elif source==10 and (load in (8,9,10) or function not in (0,6)):reason='memory DATA address/write dependencies need another hold proof'
        elif source in (11,12) and (load in (11,12) or function==5):reason='PC can change at receiver capture'
        elif source in (13,14) and (load in (13,14) or function in (3,4)):reason='SP can change at receiver capture'
        if reason:risks.append(dict(address=address,word=word,source=source,load=load,function=function,reason=reason))
    return dict(data_words=data_words,triples=[dict(source=s,load=l,function=f,words=n) for (s,l,f),n in sorted(triples.items())],risks=risks,
                scope='All 65,536 current compiled control words. Selected stored-state sources do not change at PH3 in the admitted triples. '
                      'Result source 6 changes on PH1. Memory function 6 uses the early PC-snapshot bypass; PH3 MAR storage catches the already visible address. '
                      'Fetch uses memory with MAR fixed while PC advances. IO read input must remain stable across capture. '
                      'Other triples are rejected for separate proof; this is a current-ROM contract, not arbitrary-control qualification.')


def clock_timing(frequency_hz):
    return clock_budget(Clock(),frequency_hz=frequency_hz)


def evaluate(frequency_hz,circuits):
    timing=clock_timing(frequency_hz);period=timing['oscillator_period_min_ns'];spread=3*period-timing['phase_min_ns']
    f=Fabric(circuits/'Data-Fabric.sch').parts['devices'];sel=Selector(circuits/'Data-Selector.sch').parts['devices']
    cw=Controller().parts['devices'];sq=Sequencer().parts['devices']
    mux=f['SN74AHCT157N']['max_delay_ns'];buf=f['SN74AHCT244N']['max_delay_ns'];skew=2*buf
    delivery=4*mux+2*buf;rows=[]
    def row(name,available,terms):
        required=sum(terms.values());rows.append(dict(path=name,available_ns=available,terms_ns=terms,required_ns=required,
                                                       margin_ns=available-required,passed=available>=required))
    available=timing['phase_min_ns']-skew
    for r in memory_budget(Memory())[:3]:
        row(r['path'].replace('DATA setup','DF2 receiver setup'),available,
            {'existing_ME1_path_including_40ns_setup_and_route':r['required_ns'],
             'four_muxes_two_receive_buffers':delivery,'raise_connector_setup_from_40_to_60':20})
    row('PH2 execution selector to every receiver',available,
        {'SQ_CW_PH2_gate':sq['SN74AHCT08DR']['max_delay_ns'],'CW_ACTIVE_gate':cw['SN74AHCT08DR']['max_delay_ns'],
         'CW_export_buffer':buf,'selector_format_active_gate':sel['SN74AHCT08DR']['max_delay_ns'],
         'idle_and_fetch_muxes':2*mux,'replicated_select_buffer':buf,'fabric_delivery':delivery,
         'worst_receiver_connector_setup':60,'route_allowance':10})
    row('PH2 fetch override selector to every receiver',available,
        {'SQ_window_and_fetch_gates':2*sq['SN74AHCT08DR']['max_delay_ns'],'fetch_override_mux':mux,
         'replicated_select_buffer':buf,'fabric_delivery':delivery,'worst_receiver_connector_setup':60,'route_allowance':10})
    row('PH3 capture to earliest PH2-close DATA change',period-spread-skew,
        {'worst_receiver_connector_hold':40,'route_allowance':10})
    memory=Memory().parts['devices']
    row('PH3 IO capture to PH0 external setup',period-spread-skew,
        {'local_clock_buffers':2*buf,'IO_register_clock_q':memory['CD74AC175M96']['max_delay_ns'],
         'external_setup':40,'route_allowance':10})
    return dict(frequency_hz=frequency_hz,clock_skew_ns=skew,fabric_data_delay_ns=delivery,paths=rows,
                passed=all(r['passed'] for r in rows))


def inherited(frequency,circuits):
    timing=clock_timing(frequency);rows=[];excluded=[];skew=19
    groups=[('CW1',controller_hardware,controller_hardware.Circuit()),('SQ1',sequencer,sequencer.Circuit()),
            ('AL2',alu_flash,alu_flash.Circuit()),('RG1',register_hardware,register_hardware.Circuit()),
            ('SP1/MA1',address_hardware,address_hardware.AddressPath()),('ME1',memory_hardware,memory_hardware.Circuit())]
    for name,module,circuit in groups:
        for original in module.budget(circuit,timing=timing):
            path=original['path']
            if (name=='SP1/MA1' and 'host memory' in path) or (name=='ME1' and ('early MA1 address' in path or 'external 40 ns setup' in path)):
                excluded.append(dict(board=name,path=path,reason='Superseded by pin-derived ME1 + DF2 delivery or distributed IO interval.'));continue
            if name=='AL2' and 'release before update' in path:
                excluded.append(dict(board=name,path=path,reason='AL2 private source outputs are continuously enabled; shared-output release premise does not apply.'));continue
            interphase=path.startswith('PH') or path.startswith('Stored flags') or path.startswith('HALT')
            debit=skew if interphase else 0;available=original['available_ns']-debit
            rows.append(dict(board=name,path=path,original_available_ns=original['available_ns'],
                             distribution_skew_debit_ns=debit,available_ns=available,required_ns=original['required_ns'],
                             margin_ns=available-original['required_ns'],passed=available>=original['required_ns'],
                             kind='inherited interphase path (conservative skew debit)' if interphase else 'local interface contract'))
    rows.extend(dict(board='DF2/CD1/ME1',kind='integrated delivery/hold interval',**r) for r in evaluate(frequency,circuits)['paths'])
    return dict(frequency_hz=frequency,paths=rows,excluded=excluded,passed=all(r['passed'] for r in rows))


def review(circuits):
    path=BUILD/'microcode/microcode.rom';words=struct.unpack('<65536H',path.read_bytes());contract=source_change_risks(words)
    # Same-edge PC change and memory-address change must invalidate the hold premise.
    for word in (0x8000|(11<<11)|(10<<7)|(5<<1),0x8000|(10<<11)|(8<<7)):
        assert source_change_risks([word])['risks']
    rows=[inherited(f,circuits) for f in (8000000,4000000)]
    return dict(results=rows,microcode_sha256=digest(path),source_hold_contract=contract,
                passed=not contract['risks'] and not rows[0]['passed'] and rows[1]['passed'],
                scope='Inherited CW1/SQ1/AL2/RG1/SP1/MA1/ME1 equations plus DF2 delivery/hold intervals. '
                      'Every retained phase-separated path pays 19 ns distribution skew; local connector contracts remain fixed. '
                      'Superseded host-memory and shared-output-release assumptions are explicitly excluded. '
                       '4 MHz uses the selected ACH candidate stability and allocated C1 jitter/receiver-duty assumptions; 8 MHz is a counterfactual rejection study. '
                      'Read-source memory timing inherits the ME1 derivation and its local loading assumptions. '
                      'The hold premise requires the current compiled microcode and stable external IO read data. '
                      'No additional path completeness is claimed. C1 internal timing, PC1 carry/ripple, minimum-delay races, '
                      'reset recovery/removal, clock slew/jitter, SRAM private bus and physical loads remain separate requirements.')
