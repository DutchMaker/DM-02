"""Render engineering plots from the stored numerical arrays and results."""
from pathlib import Path
import base64
import html
import json
import struct
import zlib
import numpy as np
from scipy.interpolate import RegularGridInterpolator

HERE = Path(__file__).resolve().parent


def png(rgb):
    height, width, channels = rgb.shape
    assert channels == 3
    def chunk(kind, data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw = b''.join(b'\0'+row.tobytes() for row in rgb)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')


def main():
    fields = np.load(HERE / 'field-map.npz')
    interpolator = RegularGridInterpolator((fields['y'],fields['x']),fields['potential'])
    xmin, xmax, ymin, ymax = -1.2, 1.2, -1.53, .65
    xx, yy = np.meshgrid(np.linspace(xmin,xmax,480),np.linspace(ymax,ymin,400))
    potential = np.clip(interpolator(np.c_[yy.ravel(),xx.ravel()]).reshape(xx.shape),0,1)
    stops = np.array([0.,.05,.2,.5,1.])
    colors = np.array([[19,32,63],[32,91,146],[31,159,179],[134,211,153],[255,219,91]])
    rgb = np.stack([np.interp(potential,stops,colors[:,i]) for i in range(3)],axis=-1).astype(np.uint8)
    uri = base64.b64encode(png(rgb)).decode()
    X = lambda x: 65+(x-xmin)/(xmax-xmin)*560
    Y = lambda y: 70+(ymax-y)/(ymax-ymin)*400
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 580">',
           '<rect width="700" height="580" fill="#fff"/>',
           '<g font-family="system-ui" fill="#142333"><text x="35" y="30" font-size="19">Hypothetical grounded coplanar cross-section</text>',
           '<text x="35" y="52" font-size="13">Electrostatic potential; signal = 1 V, all ground conductors = 0 V</text></g>',
           f'<image x="65" y="70" width="560" height="400" preserveAspectRatio="none" href="data:image/png;base64,{uri}"/>']
    for lo, hi, color in [(xmin,-.375,'#bec4c8'),(-.125,.125,'#ffdb5b'),(.375,xmax,'#bec4c8')]:
        out.append(f'<rect x="{X(lo)}" y="{Y(.035)}" width="{X(hi)-X(lo)}" height="{Y(0)-Y(.035)}" fill="{color}" stroke="#fff" stroke-width=".7"/>')
    out.append('<g font-family="system-ui" font-size="14" fill="#fff">')
    for x, text in [(-.85,'GND'),(0.,'Signal'),(.85,'GND')]:
        out.append(f'<text x="{X(x)}" y="{Y(.16)}" text-anchor="middle">{text}</text>')
    out += [f'<text x="{X(-1.1)}" y="{Y(.45)}">Air, εr = 1</text>',
            f'<text x="{X(-1.1)}" y="{Y(-1.2)}">Substrate, assumed εr = 4.8</text></g>',
            '<rect x="65" y="470" width="560" height="5" fill="#77818a"/>',
            '<g font-family="system-ui" font-size="13" fill="#142333">',
            '<text x="65" y="498">Lower ground plane at −1.53 mm</text>',
            '<text x="65" y="522">Trace width 0.25 mm · gaps 0.25 mm · copper thickness 0.035 mm</text>',
            '<text x="65" y="546">Crop shown: x = −1.2…1.2 mm, y = −1.53…0.65 mm.</text>',
            '<text x="65" y="568">Numerical box extends to ±12 mm horizontally and +12 mm vertically.</text></g></svg>']
    (HERE / 'field.svg').write_text('\n'.join(out))
    data = json.loads((HERE / 'numerical-results.json').read_text())
    survey = json.loads((HERE / 'survey.json').read_text())
    longest = max(survey['roots'],key=lambda r:r['length_mm'])
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 430">',
           '<rect width="760" height="430" fill="#fff"/>',
           '<g font-family="system-ui" fill="#142333">',
           '<text x="25" y="32" font-size="20">Equivalent uniform trace for the longest root</text>',
           f'<text x="25" y="56" font-size="13">{longest["length_mm"]:.3f} mm × model C′; not an extraction of ROOT3_1</text>']
    scale = 72
    for index,row in enumerate(data['scenarios']):
        y = 90+index*35
        value = row['capacitance_pf_per_mm']*longest['length_mm']
        label = row['kind'].replace('-',' ')+' · εr '+str(row['parameters']['er'])
        color = '#247e9b' if row['parameters']['er']==4. else '#7259ad'
        out.append(f'<text x="25" y="{y+15}" font-size="13">{html.escape(label)}</text>')
        out.append(f'<rect x="285" y="{y}" width="{value*scale}" height="22" fill="{color}"/>')
        out.append(f'<text x="690" y="{y+16}" font-size="13">{value:.3f}</text>')
    out += ['<text x="690" y="79" font-size="12">pF</text>',
            f'<path d="M{285+5*scale},78 V374" stroke="#b0440b" stroke-width="2" stroke-dasharray="5,4"/>',
            f'<text x="{285+5*scale}" y="398" text-anchor="middle" font-size="13">5 pF allocation</text>',
            '<text x="25" y="419" font-size="12">Pads, vias, coating, mutual coupling and three-dimensional discontinuities are omitted.</text></g></svg>']
    (HERE / 'sensitivity.svg').write_text('\n'.join(out))
    print('Rendered numerical field and equivalent-length sensitivity plots')


if __name__ == '__main__':
    main()
