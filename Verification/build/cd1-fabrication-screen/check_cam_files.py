"""Verify serialized CAM faults are detected after independent parsing."""
from pathlib import Path
import json
import shutil
from audit_cam import HERE, CAM, parse, verify


def main():
    native=json.loads((HERE/'native-cam-geometry.json').read_text())
    source=json.loads((HERE/'sources/p2-geometry.json').read_text())
    results=[]
    for fault in ('drill-coordinate','drill-plating','outline-endpoint','mask-aperture'):
        folder=HERE/'cam-faults'/fault
        folder.mkdir(parents=True,exist_ok=True)
        for path in CAM.iterdir():
            if path.is_file():shutil.copyfile(path,folder/path.name)
        if fault.startswith('drill'):
            path=next(folder.glob('*-PTH.drl'));text=path.read_text()
            before,after=('X34.4Y-50.25','X34.5Y-50.25') if fault=='drill-coordinate' else (
                'TF.FileFunction,Plated,1,2,PTH','TF.FileFunction,NonPlated,1,2,NPTH')
        elif fault=='outline-endpoint':
            path=next(folder.glob('*.gm1'));text=path.read_text()
            before,after='X20000000Y-20000000D02*','X20100000Y-20000000D02*'
        else:
            path=next(folder.glob('*.gts'));text=path.read_text()
            before,after='C,1.701600','C,1.600000'
        assert before in text,(fault,path,before)
        path.write_text(text.replace(before,after,1))
        try:
            _,records,_,_=parse(folder)
            verify(records,native,source)
        except AssertionError as error:
            results.append(dict(fault=fault,detected=True,file=str(path.relative_to(HERE)),diagnostic=str(error)))
        else:raise AssertionError('Serialized CAM mutation escaped '+fault)
    (HERE/'cam-file-fault-checks.json').write_text(json.dumps(dict(passed=True,checks=results),indent=2)+'\n')
    print('Four serialized CAM faults detected after parsing')


if __name__=='__main__':main()
