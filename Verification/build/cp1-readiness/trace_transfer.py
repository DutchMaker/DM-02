"""Add observation-only first-three-cycle traces to retained capture experiments."""
from pathlib import Path
import json
import shutil
import subprocess
from frequency_sweep import HERE,sha,write

def main():
    for mhz,ppm in ((4,0),(5,30),(6,30)):
        label=f'f{mhz}-c1-d0.5-cases0-ppm{ppm}'
        source=HERE/'sweep-capture'/label
        receipt=json.loads((source/'result.json').read_text())
        dest=HERE/'trace'/label
        assert not dest.exists(),'Preserve existing trace'
        dest.mkdir(parents=True)
        for name,h in receipt['output_hashes'].items():
            p=source/name;assert sha(p)==h
            if p.suffix in ('.sv','.hex','.bin','.txt'):shutil.copyfile(p,dest/name)
        bench=(dest/'tb.sv').read_text()
        trace='''
 always @(phase or mar or data_bus or functions or mem_n)
   if(reset_n && monitor && checked<3)
     $display("TRACE ns=%0.3f checked=%0d phase=%b mar=%h data=%h functions=%h mem_n=%b",$realtime,checked,phase,mar,data_bus,functions,mem_n);
'''
        assert bench.count('\nendmodule')==1
        (dest/'tb.sv').write_text(bench.replace('\nendmodule',trace+'\nendmodule'))
        p=subprocess.run(receipt['command'],cwd=dest,capture_output=True,text=True,timeout=120)
        assert p.returncode==0,p.stderr
        p=subprocess.run(['vvp','simulation.vvp'],cwd=dest,capture_output=True,text=True,timeout=300)
        (dest/'simulation.log').write_text(p.stdout+p.stderr)
        write(dest/'result.json',dict(parent=str(source.relative_to(HERE)),parent_receipt_sha256=sha(source/'result.json'),
            command=receipt['command'],exit_code=p.returncode,observation_only=True,
            hashes={q.name:sha(q) for q in dest.iterdir() if q.is_file() and q.suffix!='.vvp'}))
        print(label,p.returncode,flush=True)

if __name__=='__main__':main()
