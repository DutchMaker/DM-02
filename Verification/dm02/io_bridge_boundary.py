"""Explicit R2 local-net / CN1 / bridge bindings; not full CPU integration."""
from . import connector_plan
from .io_bridge import require


def audit(circuit, boundary=None, plan=None):
    baseline=connector_plan.native_boundary() if boundary is None else boundary
    plan=connector_plan.generate(baseline) if plan is None else plan
    connector_plan.validate(plan)
    bindings=[]
    def bind(board,ref,pin,signal,assembly,old_board,old_ref,old_pin,local):
        require(circuit.boundary[board][ref][str(pin)]==signal,'Changed bridge boundary declaration')
        require(circuit.nets[circuit.n(board,ref,pin)]['name']==signal,'Bridge native boundary mismatch')
        endpoints=[e for e in baseline['nets'][assembly] if (e['board'],e['connector'],e['pin'])==
                   (old_board,old_ref,str(old_pin))]
        require(len(endpoints)==1 and endpoints[0]['local_net']==local,'R2 local/assembly binding mismatch')
        bindings.append(dict(board=board,connector=ref,pin=str(pin),signal=signal,
            assembly_net=assembly,r2_endpoint=endpoints[0]))
    for bit in range(16):
        bind('MQ1','J1',bit+3,f'ADDRESS{bit}',f'ADDRESS{bit}','ME1','J3',bit+3,f'ADDRESS{bit}')
        require(any(e['board']=='MA1' for e in baseline['nets'][f'ADDRESS{bit}']), 'Missing MAR source')
    for pin,signal,old_pin,local in ((19,'MEM_n',7,'MEM_out_n'),(20,'LOAD_n10',8,'MEM_load_n'),
                                    (21,'ME1_RESET_n',6,'RESET_n')):
        bind('MQ1','J1',pin,signal,signal,'ME1','J1',old_pin,local)
    bind('BR1','J4',3,'RESET_n','RESET_n','C1','J90',4,'RESET_RELEASE_n')
    for bit in range(8):
        bind('BR1','J1',bit+3,f'IO_ADDRESS{bit}',f'IO_ADDRESS{bit}','ME1','J4',bit+12,f'IO_ADDR{bit}')
        bind('BR1','J1',bit+11,f'IO_DATA{bit}',f'IO_DATA{bit}','ME1','J4',bit+4,f'IO_DATA{bit}')
        bind('BR1','J3',bit+3,f'IO_INPUT{bit}',f'IO_INPUT{bit}','ME1','J5',bit+3,f'IO_INPUT{bit}')
    bind('BR1','J1',19,'IO_STROBE','IO_STROBE','ME1','J4',3,'IO_STROBE')
    memory=next(c for c in plan['cpu_cards'] if c['role']=='memory')
    contacts={p['net']:dict(connector=c['ref'],pin=p['pin']) for c in memory['connectors']
              for p in c['pins'] if p['kind']=='signal'}
    extensions=[]
    for pin,signal in enumerate([f'LIVE_ADDRESS{i}' for i in range(16)]+['IO_READ_VALID'],3):
        require(signal in contacts,'Missing CN1 memory extension')
        for board in ('MQ1','BR1'):
            require(circuit.boundary[board]['J2'][str(pin)]==signal,'Extension declaration mismatch')
            require(circuit.nets[circuit.n(board,'J2',pin)]['name']==signal,'Extension native mismatch')
        extensions.append(dict(signal=signal,logical_pin=str(pin),**contacts[signal]))
    for row in bindings:
        if row['board']=='MQ1' and not row['signal'].startswith('ADDRESS'):
            require(row['assembly_net'] in contacts,'MQ1 input requires an unallocated card crossing')
    checked=0
    for card in plan['peripheral_cards']:
        ref=f'J{card["position"]}'
        for pin in card['connector']['pins']:
            actual=circuit.nets[circuit.n('BR1',ref,pin['pin'])]['name']
            require(actual==pin['net'] if pin['net'] is not None else actual.startswith('unconnected-'),
                    'Peripheral native contact differs from CN1')
            checked+=1
    return dict(passed=True,baseline_revision='CP1-R2',revision='CP1-BR1',bindings=bindings,
        memory_extensions=extensions,peripheral_contacts_checked=checked,source_hashes=baseline['source_hashes'],
        physical_qualification=False,integrated_into_R2=False,
        reset_scope='MQ1 uses ME1_RESET_n at memory J1.6; BR1 uses C1 reset root. Their nets must not be shorted. Sampled 70 ns branch skew is not timing qualification.')
