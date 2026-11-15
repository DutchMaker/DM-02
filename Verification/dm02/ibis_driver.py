"""Qualify the exact pilot driver's IBIS input before transient extrapolation.

Vendor files and derived decks stay outside the served Verification tree.
This is a restricted HCT245 reader, not a general IBIS simulator.
"""
import bisect
import hashlib
import re
import subprocess

MODEL_HASH = '80938faeab0e16bac1b0c4e319376c6f3f30a358eb5b74c53019449ffe58a177'
CHECKER_SHA1 = '71ee5d76b317933ca67d5a69d99e822200c34403'
CORNERS = ('typ', 'min', 'max')


def number(s):
    if s == 'NA':
        return None
    match = re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)(.*)', s)
    assert match, s
    tail = match[2].lower()
    scale = {'': 1, 'v': 1, 's': 1, 'pf': 1e-12, 'nh': 1e-9}[tail]
    return float(match[1]) * scale


def sections(text):
    result = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split('|')[0].strip()
        if not line:
            continue
        match = re.match(r'^\[([^]]+)\]\s*(.*)', line)
        if match:
            result.append(dict(key=match[1], value=match[2], line=lineno, rows=[]))
        else:
            assert result
            result[-1]['rows'].append((lineno, line))
    return result


def model_data(text):
    all_sections = sections(text)
    start = next(i for i, s in enumerate(all_sections) if s['key'] == 'Model' and s['value'] == 'HCT245_IO')
    data = all_sections[start:]
    one = lambda key: next(s for s in data if s['key'] == key)
    tables = {}
    for key in ('Pullup', 'Pulldown', 'GND Clamp', 'POWER Clamp'):
        table = sorted([list(map(number, row.split())) for _, row in one(key)['rows']])
        assert all(len(row) == 4 and all(v is not None for v in row) for row in table)
        assert all(a[0] < b[0] for a, b in zip(table, table[1:]))
        tables[key] = table
    waves = []
    for section in data:
        if section['key'] not in ('Rising Waveform', 'Falling Waveform'):
            continue
        params, rows = {}, []
        for _, line in section['rows']:
            if '=' in line:
                key, value = line.split('=')
                params[key.strip()] = number(value.strip())
            else:
                rows.append(list(map(number, line.split())))
        assert all(a[0] < b[0] for a, b in zip(rows, rows[1:]))
        waves.append(dict(edge=section['key'].split()[0].lower(), line=section['line'], params=params, rows=rows))
    assert len(waves) == 4
    comp = next(line for _, line in data[0]['rows'] if line.startswith('C_comp')).split()[1:]
    assert number(comp[0]) > 0, 'Nonpositive typical output capacitance'
    return dict(tables=tables, waves=waves, capacitance=list(map(number, comp)),
                voltage=list(map(number, one('Voltage Range')['value'].split())),
                temperature=list(map(number, one('Temperature Range')['value'].split())))


def package_check(text):
    all_sections = sections(text)
    start = next(i for i, s in enumerate(all_sections) if s['key'] == 'Component' and s['value'] == 'HCT245_N')
    pin_section = next(s for s in all_sections[start:] if s['key'] == 'Pin')
    pins = [row.split() for _, row in pin_section['rows']]
    assert {int(row[0]) for row in pins} == set(range(1, 21))
    signals = {int(row[0]): row[1:3] for row in pins}
    assert signals[1] == ['DIR', 'HCT245_DIR'] and signals[19] == ['NOE', 'HCT245_NOE']
    assert signals[10] == ['GND', 'GND'] and signals[20] == ['VCC', 'POWER']
    for bit in range(1, 9):
        assert signals[bit+1] == [f'A{bit}', 'HCT245_IO']
        assert signals[19-bit] == [f'B{bit}', 'HCT245_IO']
    values = [list(map(number, row[3:])) for row in pins if row[2] == 'HCT245_IO']
    assert all(len(row) == 3 and all(v > 0 for v in row) for row in values)
    return dict(component='HCT245_N', pins=20, data_pins=16, pin_roles_checked=True,
        data_pin_r_ohm_range=[min(r[0] for r in values), max(r[0] for r in values)],
        data_pin_l_nh_range=[min(r[1] for r in values)*1e9, max(r[1] for r in values)*1e9],
        data_pin_c_pf_range=[min(r[2] for r in values)*1e12, max(r[2] for r in values)*1e12])


def interp(table, x, column):
    # IBIS tables may cover only the active clamp region. At a missing tail,
    # retain the endpoint current; do not create an extrapolated diode slope.
    if x <= table[0][0]:
        return table[0][column]
    if x >= table[-1][0]:
        return table[-1][column]
    i = bisect.bisect_right([row[0] for row in table], x) - 1
    a, b = table[i:i+2]
    return a[column] + (b[column]-a[column]) * (x-a[0])/(b[0]-a[0])


def current(data, v, column, state):
    supply = data['voltage'][column-1]
    tables = data['tables']
    # Positive current flows INTO the die. Pullup/power-clamp coordinates
    # are VCC - Vpad; pulldown/ground-clamp coordinates are Vpad - GND.
    drive = interp(tables['Pullup'], supply-v, column) if state == 'high' else interp(tables['Pulldown'], v, column)
    return drive + interp(tables['GND Clamp'], v, column) + interp(tables['POWER Clamp'], supply-v, column)


def root(fn, low, high):
    assert fn(low) < 0 < fn(high), 'Unbracketed DC equilibrium'
    for _ in range(80):
        mid = (low+high)/2
        if fn(mid) > 0:
            high = mid
        else:
            low = mid
    return (low+high)/2


def crossing(rows, column, threshold, rising):
    # Last entry into the valid region: ignores early crossings followed by
    # ringing back across the threshold. None means no stable crossing.
    valid = lambda v: v >= threshold if rising else v <= threshold
    if not valid(rows[-1][column]):
        return None
    last_bad = next((i for i in range(len(rows)-1, -1, -1) if not valid(rows[i][column])), None)
    if last_bad is None:
        return rows[0][0]
    a, b = rows[last_bad:last_bad+2]
    return a[0] + (b[0]-a[0]) * (threshold-a[column])/(b[column]-a[column])


def endpoint_audit(data):
    endpoints, edges = [], []
    for wave in data['waves']:
        p = wave['params']
        assert p['C_fixture'] == 0 and p['L_fixture'] == 0
        for column, corner in enumerate(CORNERS, 1):
            vcc = data['voltage'][column-1]
            fixture = p['V_fixture' + ('' if corner == 'typ' else '_'+corner)]
            for end, index in (('start', 0), ('end', -1)):
                state = 'high' if (wave['edge'] == 'rising') == (end == 'end') else 'low'
                v = wave['rows'][index][column]
                fn = lambda x: current(data, x, column, state) + (x-fixture)/p['R_fixture']
                equilibrium = root(fn, -0.1, vcc+0.3)
                endpoints.append(dict(wave_line=wave['line'], edge=wave['edge'], corner=corner, end=end, state=state,
                    supply_v=vcc, fixture_v=fixture, resistance_ohm=p['R_fixture'], waveform_v=v,
                    iv_equilibrium_v=equilibrium, difference_v=v-equilibrium,
                    kcl_residual_ma=1000*fn(v)))
            threshold = 2.0 if wave['edge'] == 'rising' else 0.8
            t = crossing(wave['rows'], column, threshold, wave['edge'] == 'rising')
            capture = interp(wave['rows'], 25e-9, column)
            edges.append(dict(wave_line=wave['line'], edge=wave['edge'], corner=corner, fixture_v=fixture,
                fixture_r_ohm=p['R_fixture'], fixture_cap_pf=0,
                stable_threshold_ns=None if t is None else t*1e9, threshold_v=threshold,
                voltage_at_waveform_25ns=capture,
                valid_at_waveform_25ns=capture >= threshold if wave['edge'] == 'rising' else capture <= threshold))
    return endpoints, edges


def pwl_expression(table, column, variable):
    # Equivalent linear-segment expansion; avoids reliance on a SPICE-specific
    # lookup-table primitive. Constant endpoint extrapolation matches interp.
    terms = [f'{table[0][column]:.16g}']
    prev = 0
    for a, b in zip(table, table[1:]):
        slope = (b[column]-a[column])/(b[0]-a[0])
        terms.append(f'({slope-prev:.16g})*max(0,({variable})-({a[0]:.16g}))')
        prev = slope
    terms.append(f'({-prev:.16g})*max(0,({variable})-({table[-1][0]:.16g}))')
    return '+'.join(terms)


def spice_crosscheck(data, endpoints, private):
    rows = []
    # Independent nonlinear solver checks every distinct fixture/state/corner.
    for corner_index, corner in enumerate(CORNERS, 1):
        vcc = data['voltage'][corner_index-1]
        for state in ('low', 'high'):
            for fixture in (0, vcc):
                expressions = []
                for key, variable in ((('Pullup' if state == 'high' else 'Pulldown'), f'{vcc}-v(out)' if state == 'high' else 'v(out)'),
                                      ('GND Clamp', 'v(out)'), ('POWER Clamp', f'{vcc}-v(out)')):
                    expressions.append(pwl_expression(data['tables'][key], corner_index, variable))
                name = f'{corner}-{state}-fixture{fixture:g}'
                deck = '* Local IBIS-derived DC consistency circuit\n'
                deck += f'Vfixture fixture 0 {fixture}\nRload out fixture 1000\n'
                for i, expr in enumerate(expressions):
                    deck += f'B{i} out 0 I={expr}\n'
                deck += f'.nodeset v(out)={vcc if state == "high" else 0}\n'
                deck += '.options abstol=1e-12 reltol=1e-9\n.control\nop\nprint v(out)\nquit\n.endc\n.end\n'
                path = private/(name+'.cir'); path.write_text(deck)
                result = subprocess.run(['ngspice', '-b', str(path)], capture_output=True, text=True, timeout=30)
                log = result.stdout + result.stderr
                (private/(name+'.log')).write_text(log)
                match = re.search(r'v\(out\)\s*=\s*([-+\d.eE]+)', log)
                assert result.returncode == 0 and match, (name, log)
                v = float(match[1])
                expected = next(r['iv_equilibrium_v'] for r in endpoints if r['corner'] == corner and r['state'] == state and r['fixture_v'] == fixture)
                assert abs(v-expected) < 2e-6, (name, v, expected)
                rows.append(dict(case=name, ngspice_v=v, bisection_v=expected, difference_v=v-expected, passed=True))
    return rows


def checker_run(checker, model):
    result = subprocess.run([str(checker), '-caution', '-numbered', str(model)], capture_output=True, text=True, timeout=60)
    log = result.stdout + result.stderr
    # This executable returns zero even for a failed file: parse its verdict.
    assert 'IBISCHK7 V7.2.1' in log
    errors=int(re.search(r'Errors\s*:\s*(\d+)', log)[1])
    return dict(exit_code=result.returncode, passed=result.returncode==0 and errors==0 and 'File Passed' in log and 'File Failed' not in log,
                errors=errors), log


def qualify(model, checker, private, output):
    """Rerun official syntax and DC checks against the pinned original bytes."""
    raw = model.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MODEL_HASH
    assert hashlib.sha1(checker.read_bytes()).hexdigest() == CHECKER_SHA1
    private.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    original_result, original_log = checker_run(checker, model)
    (output/'ibischk-original.log').write_text(original_log)
    assert raw.endswith(b'\xff') and raw.count(b'\xff') == 1
    normalized = private/'sn74hct245.ibs'
    normalized.write_bytes(raw[:-1])
    normalized_result, normalized_log = checker_run(checker, normalized)
    (output/'ibischk-normalized.log').write_text(normalized_log)
    assert normalized_result['passed'] and normalized_result['errors'] == 0
    text = normalized.read_text(encoding='ascii')
    package = package_check(text)
    data = model_data(text)
    endpoints, edges = endpoint_audit(data)
    spice = spice_crosscheck(data, endpoints, private)
    result = dict(audit_completed=True, selected_mpn='SN74HCT245N',
        model_url='https://www.ti.com/lit/ibs/SCLM097', model_sha256=MODEL_HASH,
        checker_url='https://www.ibis.org/ibischk7/ibischk721_maca_64.zip', checker_sha1=CHECKER_SHA1,
        original_checker=original_result, normalized_checker=normalized_result,
        normalization='Filename changed to sn74hct245.ibs and sole trailing 0xff byte removed. Numeric data unchanged.',
        normalized_sha256=hashlib.sha256(normalized.read_bytes()).hexdigest(),
        package=package,
        corners=[dict(name=c, voltage_v=data['voltage'][i], temperature_c=data['temperature'][i], c_comp_pf=None if data['capacitance'][i] is None else data['capacitance'][i]*1e12) for i, c in enumerate(CORNERS)],
        endpoints=endpoints, waveform_thresholds=edges, independent_dc_checks=spice,
        worst_endpoint_difference_v=max(abs(r['difference_v']) for r in endpoints),
        interpretation='Endpoint differences are diagnostics, not an IBISCHK failure or a new acceptance tolerance. Fixture waveforms are not pilot loaded-output predictions.',
        limitations=[
            'C_comp is 4 pF typical; min/max values are NA. No full-envelope output-capacitance bound.',
            'Header says measurements used the NS package. N (PDIP) parasitics exist, but waveform measurement pin/de-embedding is unspecified.',
            'Waveforms use 1 kohm resistors and zero fixture capacitance. Cref=50 pF describes a timing reference, not these waveform loads.',
            'Waveform time origin is not a guaranteed input-to-output propagation bound; the 25 ns diagnostic uses the file clock only.',
            'Three paired process/voltage/temperature columns do not establish every 4.75–5.25 V, 0–50 C condition.',
            'IBIS syntax pass and DC parity do not establish transient correlation, receiver load, output-enable handover or physical qualification.'
        ])
    return text, result
