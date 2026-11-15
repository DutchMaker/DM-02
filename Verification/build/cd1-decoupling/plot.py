"""Draw per-device layout details from measured P3 geometry."""
from pathlib import Path
import json
import html
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ground',HERE/'sources/ground-audit.py')
ground=importlib.util.module_from_spec(spec);spec.loader.exec_module(ground)
data=json.loads((HERE/'geometry.json').read_text())
plan=json.loads((HERE/'generation.json').read_text())
planes,_=ground.plane_geometry(data)
out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 930 540">',
 '<rect width="930" height="540" fill="#fff"/>',
 '<text x="25" y="28" font-family="system-ui" font-size="18" fill="#142333">P3 local capacitor feeds · front copper</text>']
for i,row in enumerate(plan['capacitors']):
    vcc=next(p for p in data['pads'] if p['ref']==row['ic'] and p['pin']=='20')
    x,y=vcc['position'];left=x-13;top=y-5
    out.append(f'<svg x="{20+305*i}" y="48" width="285" height="420" viewBox="{left} {top} 21 31">')
    out.append(f'<rect x="{left}" y="{top}" width="21" height="31" fill="#eaf1ee"/>')
    for poly in ground.polygons(planes['F.Cu']):
        d=[]
        for r in (poly.exterior,*poly.interiors):d.append('M'+' L'.join(f'{a},{b}' for a,b in r.coords)+' Z')
        out.append(f'<path d="{" ".join(d)}" fill="#c0dccd" fill-rule="evenodd"/>')
    for t in data['tracks']:
        if t['layer']!='F.Cu':continue
        color='#e07b22' if t['net']=='/5V' else '#7897ad' if t['net']!='/GND' else '#779987'
        a,b=t['start'],t['end']
        out.append(f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" stroke="{color}" stroke-width="{t["width_mm"]}"/>')
    for p in data['pads']:
        a,b=p['position'];color='#cf650e' if p['net']=='/5V' else '#287247' if p['net']=='/GND' else '#75808c'
        out.append(f'<circle cx="{a}" cy="{b}" r=".8" fill="{color}"/><circle cx="{a}" cy="{b}" r=".4" fill="#fff"/>')
    for v in data['vias']:
        a,b=v['position'];color='#cf650e' if v['net']=='/5V' else '#287247' if v['net']=='/GND' else '#75808c'
        out.append(f'<circle cx="{a}" cy="{b}" r="{v["diameter_mm"]/2}" fill="{color}"/><circle cx="{a}" cy="{b}" r="{v["drill_mm"]/2}" fill="#fff"/>')
    for p in data['pads']:
        if (p['ref']==row['ic'] and p['pin'] in ('20','10')) or p['ref']==row['ref']:
            a,b=p['position'];label=f'{p["ref"]}.{p["pin"]}'
            dx=-2 if p['ref']==row['ic'] else 1.1
            anchor='end' if dx<0 else 'start'
            out.append(f'<text x="{a+dx}" y="{b+.25}" text-anchor="{anchor}" font-size=".8" font-family="system-ui" fill="#142333">{html.escape(label)}</text>')
    # The body drawing uses manufacturer maximum L/T around nominal lead pitch.
    cap=next(p for p in data['pads'] if p['ref']==row['ref'] and p['pin']=='1')
    a,b=cap['position']
    out.append(f'<rect x="{a-1.27}" y="{b-.635}" width="2.54" height="3.81" fill="none" stroke="#572d80" stroke-width=".12"/>')
    out.append('</svg>')
    feed=plan['added_tracks'][i];length=sum((b-a)**2 for a,b in zip(feed['start'],feed['end']))**.5
    out.append(f'<text x="{35+305*i}" y="490" font-family="system-ui" font-size="15" fill="#142333">{row["ic"]} / {row["ref"]}: {length:.3f} mm × 0.50 mm</text>')
out.append('<text x="25" y="525" font-family="system-ui" font-size="13" fill="#142333">Orange: supply copper · green: ground fill/pads · purple: capacitor body maximum · GND is IC pin 10.</text></svg>')
(HERE/'feeds.svg').write_text('\n'.join(out))
print('Rendered three native-geometry feed details')
