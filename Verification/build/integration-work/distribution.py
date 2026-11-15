"""Normal FD1 stage: pin-derived distribution, intervals, loads and execution."""
from designs.distribution_candidate import generate,SOURCE
from .common import BUILD,digest,evidence,write_json
from .legacy import read_sheet
from .electrical import audit as structural_audit
from .native_migrate import validate
from .distribution_links import audit as link_audit
from .distribution_run import profile,fixtures,opcode_fixtures,demo_fixtures,render
from .distribution_checks import wiring_faults,receiver_guards
from .distribution_timing import review


def run():
    folder=BUILD/'distribution';circuits=folder/'circuits';generated=generate(circuits)
    construction=[]
    for name,path in generated.items():
        source=SOURCE/path.name
        if source.read_bytes()!=path.read_bytes():raise ValueError('FD1 candidate differs from generator: '+str(source))
        sheet=read_sheet(source)
        construction.append(dict(board=name,source=sheet['source'],source_sha256=digest(source),
                                 structure=structural_audit(sheet),native=validate(sheet,folder/'native'/name)))
    links=link_audit(SOURCE);timing=review(SOURCE)
    fixture=folder/'fixtures';coverage=fixtures(fixture);opcodes=opcode_fixtures(fixture)
    continuous=[profile(SOURCE,folder/f'continuous-{logic}-{tree}-{fabric}',fixture,logic,tree,fabric)
                for logic,tree,fabric in ((0,0,0),(0,1,1),(1,0,0),(1,1,1),(1,2,2),(2,3,3),(3,4,4),(4,5,5))]
    instructions=[profile(SOURCE,folder/f'opcodes-{corner}',fixture,corner,corner,corner,cases=True) for corner in (0,1,2)]
    hello_fixture=folder/'hello-fixture';hello_coverage=demo_fixtures(hello_fixture,'hello_world')
    hello=profile(SOURCE,folder/'hello',hello_fixture,demo=True)
    output=render(folder/'hello','hello_world') if hello['passed'] else dict(passed=False)
    faults=wiring_faults(SOURCE,folder/'faults',fixture);guards=receiver_guards(folder/'faults')
    passed=(all(not r['structure']['findings'] and r['native']['status']=='pass' for r in construction) and
            links['passed'] and timing['passed'] and all(r['passed'] for r in continuous+instructions+[hello]) and
            output['passed'] and output.get('io_events')==hello_coverage['io_events'] and
            all(r['detected'] for r in faults) and all(r['passed'] for r in guards))
    result=dict(passed=passed,construction=construction,links=links,timing=timing,coverage=coverage,opcode_coverage=opcodes,
                continuous=continuous,opcodes=instructions,hello=dict(simulation=hello,coverage=hello_coverage,output=output),
                wiring_faults=faults,receiver_guards=guards)
    write_json(folder/'summary.json',result);write_json(folder/'links.json',links);write_json(folder/'timing.json',timing)
    return evidence('distribution','FD1 flash machine with clock/reset and private DATA distribution','limited' if passed else 'fail',
        f'{sum(r["passed"] for r in continuous)}/8 continuous and {sum(r["passed"] for r in instructions)}/3 all-opcode profiles; '
        f'{len(links["rows"])} connector links; {sum(r["detected"] for r in faults)}/9 wiring mutations and '
        f'{sum(r["passed"] for r in guards)}/28 receiver guards; conditional 4 MHz target, 8 MHz rejected.',
        limitation='AL2 occupies the AL1 connector slot. Each link allocates 10 pF total trace/connector load. '
                   'Partial interval/load coverage, exact oscillator, qualified reset, private SRAM turnaround, full-temperature '
                   'capacitance and physical routing remain open. No physical-clock or MOD-08 acceptance is implied.',
        artifacts=['distribution/summary.json','distribution/links.json','distribution/timing.json',
                   'distribution/faults/wiring.json','distribution/faults/guards.json','distribution/hello/io-observed.txt']+
                  [f'distribution/native/{r["board"]}/{r["native"]["sheet"]}.kicad_sch' for r in construction])
