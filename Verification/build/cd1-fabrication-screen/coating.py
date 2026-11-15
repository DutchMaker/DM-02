"""Supplier-anchored dimensions and hypothetical planar coating sensitivity.

The coating fills all space from the substrate surface to a flat top above
the copper. This is a hypothetical morphology, not the actual purple mask.
"""
from pathlib import Path
import importlib.util
import json
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('archived_field',HERE/'sources/field.py')
field=importlib.util.module_from_spec(spec);spec.loader.exec_module(field)


def coated(height=1.524,er=4.5,thickness=.03556,coat=.01524,coat_er=4.5,
           minimum=.00125,growth=1.08,box=12.):
    width=gap=.25
    edge=width/2+gap
    top=thickness+coat
    x=field.graded_axis([-box,-edge,-width/2,0.,width/2,edge,box],minimum,growth)
    y=field.graded_axis([-height,0.,thickness,top,box],minimum,growth)
    xx,yy=np.meshgrid(x,y)
    copper=(yy>=-1e-12)&(yy<=thickness+1e-12)
    signal=(abs(xx)<=width/2+1e-12)&copper
    ground=(abs(xx)>=edge-1e-12)&copper
    ground[[0,-1],:]=True;ground[:,[0,-1]]=True
    layers=[(-height,0.,er),(0.,top,coat_er),(top,box,1.)]
    return field.solve(x,y,layers,ground|signal,signal.astype(float),signal)


def main():
    base=dict(height=1.524,er=4.5,thickness=.03556,minimum=.00125,growth=1.08,box=12.)
    rows=[]
    def run(name,coating=False,**overrides):
        args=dict(base,**overrides)
        value=coated(**args) if coating else field.cross_section(**args)
        row=dict(name=name,planar_coating=coating,parameters=args,**value)
        rows.append(row)
        print(name,value['capacitance_pf_per_mm'],flush=True)
        return row
    nominal=run('service nominal, uncoated')
    run('thin published core, uncoated',height=1.3716)
    run('thick published core, uncoated',height=1.6764)
    run('material typical 1 MHz, uncoated',er=4.8)
    run('material specification number, uncoated',er=5.4)
    for thickness in (.01016,.01524,.02032):
        run('hypothetical flat coating %.5f mm'%thickness,coating=True,coat=thickness,coat_er=4.5)
    run('material 4.8 plus hypothetical nominal coating',coating=True,er=4.8,coat=.01524,coat_er=4.5)
    # A unity-er coating must recover the archived air model; the extra grid
    # interface can cause a small discretization difference, measured here.
    air=coated(**base,coat=.01524,coat_er=1.)
    unity_error=abs(air['capacitance_pf_per_mm']/nominal['capacitance_pf_per_mm']-1)
    assert unity_error<.001
    target=next(r for r in rows if r['name']=='hypothetical flat coating 0.01524 mm')
    coarse=coated(**dict(base,minimum=.0025),coat=.01524,coat_er=4.5)
    fine=coated(**dict(base,minimum=.000625),coat=.01524,coat_er=4.5)
    box=coated(**dict(base,box=24.),coat=.01524,coat_er=4.5)
    mesh_change=abs(fine['capacitance_pf_per_mm']/target['capacitance_pf_per_mm']-1)
    box_change=abs(box['capacitance_pf_per_mm']/target['capacitance_pf_per_mm']-1)
    assert mesh_change<.005 and box_change<.005
    assert fine['capacitance_pf_per_mm']<target['capacitance_pf_per_mm']<coarse['capacitance_pf_per_mm']
    survey=json.loads((HERE/'sources/survey.json').read_text())
    longest=max(survey['roots'],key=lambda r:r['length_mm'])
    for row in rows:
        row['longest_root_equivalent_pf']=row['capacitance_pf_per_mm']*longest['length_mm']
        row['allocation_remaining_pf']=5-row['longest_root_equivalent_pf']
    checks=dict(unity_er_coating_relative_difference=unity_error,coarse=coarse,fine=fine,expanded_box=box,
                final_mesh_relative_change=mesh_change,box_relative_change=box_change)
    result=dict(passed=True,scenarios=rows,checks=checks,longest_root_length_mm=longest['length_mm'],
        geometry='0.25 mm trace and gap; continuous coplanar and opposite ground; nominal copper 0.03556 mm.',
        coating_geometry='Flat dielectric slab from substrate surface to copper top plus specified coating thickness, filling the gaps.',
        scope='Sensitivity only. Core tolerance is published; copper tolerance is unknown. Green-mask 1 MHz data is hypothetical for this purple service. No broadband board bound.',
        actual_board_capacitance_qualified=False,fabrication_ready=False)
    (HERE/'coating-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Nine sensitivities complete; mesh change',mesh_change,'box change',box_change,flush=True)


if __name__=='__main__':main()
