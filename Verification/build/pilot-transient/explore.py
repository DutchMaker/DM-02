"""Inspect two-fixture IBIS switching-factor extraction before adoption."""
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('driver_audit', HERE.parent/'pilot-driver/audit.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


def sample(rows, t, col):
    for a, b in zip(rows, rows[1:]):
        if a[0] <= t < b[0]:
            slope = (b[col]-a[col])/(b[0]-a[0])
            return a[col]+slope*(t-a[0]), slope
    return rows[0 if t < rows[0][0] else -1][col], 0


def coefficients(data, edge, col, t, wave_sampler=sample):
    eqs = []
    supply = data['voltage'][col-1]
    for wave in data['waves']:
        if wave['edge'] != edge:
            continue
        v, dvdt = wave_sampler(wave['rows'], t, col)
        p = wave['params']; suffix = ('', '_min', '_max')[col-1]
        current = (v-p['V_fixture'+suffix])/p['R_fixture'] + 4e-12*dvdt
        current += audit.interp(data['tables']['GND Clamp'], v, col)
        current += audit.interp(data['tables']['POWER Clamp'], supply-v, col)
        up = audit.interp(data['tables']['Pullup'], supply-v, col)
        down = audit.interp(data['tables']['Pulldown'], v, col)
        eqs.append((up, down, -current))
    a,b = eqs
    det = a[0]*b[1]-b[0]*a[1]
    return ((a[2]*b[1]-b[2]*a[1])/det, (a[0]*b[2]-b[0]*a[2])/det, det)


if __name__ == '__main__':
    text = Path(sys.argv[1]).read_bytes().rstrip(b'\xff').decode('ascii')
    data = audit.model_data(text)
    for edge in ('rising', 'falling'):
        for col in (1,2,3):
            rows = [(i*.01, *coefficients(data, edge, col, i*.01e-9)) for i in range(5001)]
            print(edge,col, 'ku',min(r[1] for r in rows),max(r[1] for r in rows),
                  'kd',min(r[2] for r in rows),max(r[2] for r in rows),
                  'det',min(abs(r[3]) for r in rows), 'tails',rows[0],rows[-1])
