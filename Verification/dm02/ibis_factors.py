"""Extract IBIS switching factors by two fixture equations, without clipping."""
from . import ibis_driver as audit


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
