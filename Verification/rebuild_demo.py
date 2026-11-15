#!/usr/bin/env python3
"""Rebuild the graphics demo in isolation; compare committed copies, or update with --write."""
import argparse
from pathlib import Path
import shutil
import tempfile
from dm02.common import ROOT, BUILD, command, digest, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    dll=ROOT/'Code/Assembler/src/Asm/bin/Debug/netcoreapp2.2/asm.dll'
    if not dll.exists():
        raise SystemExit('First run: dotnet build Code/Assembler/src/Asm/Asm.csproj')
    source=ROOT/'Code/Assembler/programs/emulator_demo'
    targets=[source/'emulator_demo.bin',ROOT/'Code/Emulator/programs/emulator_demo.bin']
    BUILD.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='demo-',dir=BUILD) as directory:
        folder=Path(directory)
        for file in source.glob('*.asm'): shutil.copyfile(file,folder/file.name)
        args_=['dotnet','--roll-forward','Major',dll,ROOT/'Code/Microcode/microcode.src',folder/'emulator_demo.asm']
        code,log=command(args_,timeout=120)
        (BUILD/'demo-build.log').write_text(log)
        generated=folder/'emulator_demo.bin'
        if code or not generated.is_file(): raise RuntimeError('Assembler failed; inspect Verification/build/demo-build.log')
        content=generated.read_bytes()
        if args.write:
            for file in targets: file.write_bytes(content)
        rows=[dict(file=str(file.relative_to(ROOT)),matches=file.read_bytes()==content,sha256=digest(file)) for file in targets]
        result=dict(status='pass' if all(row['matches'] for row in rows) else 'fail',bytes=len(content),
                    generated_sha256=digest(generated),assembler_sha256=digest(dll),copies=rows,
                    sources={str(file.relative_to(ROOT)):digest(file) for file in source.glob('*.asm')})
        write_json(BUILD/'demo-build.json',result)
        print(result)
        return 0 if result['status']=='pass' else 1


if __name__=='__main__': raise SystemExit(main())
