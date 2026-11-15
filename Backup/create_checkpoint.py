"""Back up preserved runs and supplemental studies, without reading live stages."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'Verification/build'
LIVE={'alu','microcode','inventory','schematics','native-schematics','pilot','analog',
      'registers','memory','clock','reset','pc-hardware','controller','sequencer',
      'alu-hardware','register-hardware','address-hardware','memory-hardware',
      'hardware-programs','flash-array','alu-flash','distribution','backplane','boot'}
CACHES={'__pycache__','.venv','node_modules','bin','obj'}


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


class HashedReader:
    def __init__(self,stream):self.stream=stream;self.hash=hashlib.sha256()
    def read(self,size=-1):
        data=self.stream.read(size);self.hash.update(data);return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args();output=args.output.expanduser().resolve()
    assert not output.is_relative_to(ROOT),'Backup output must be outside the repository'
    output.mkdir(parents=True,exist_ok=True)
    groups={'completed-runs.tar.gz':[BUILD/'experiments'],
        'studies-and-workbook.tar.gz':[p for p in sorted(BUILD.iterdir()) if p.is_dir() and p.name not in LIVE|{'experiments'}]}
    for name in (*groups,'checkpoint-manifest.json'):
        assert not (output/name).exists(),'Existing checkpoint: '+str(output/name)
    manifest=dict(created_at=datetime.now(timezone.utc).isoformat(),
        repository='DutchMaker/DM-02',
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        scope='Preserved experiments and supplemental studies; live normal-stage outputs are excluded.',
        archives={},files={})
    for name,folders in groups.items():
        paths=sorted(p for folder in folders for p in folder.rglob('*') if p.is_file()
            and not any(part in CACHES for part in p.relative_to(BUILD).parts))
        assert paths
        target=output/name
        with tarfile.open(target,'w:gz',compresslevel=6) as archive:
            for path in paths:
                assert not path.is_symlink() and path.resolve().is_relative_to(BUILD)
                assert path.suffix.lower() not in {'.ibs','.ibis','.pem','.key'}
                assert path.name not in {'.env','ibischk7_64'}
                before=path.stat();relative=path.relative_to(ROOT).as_posix()
                info=archive.gettarinfo(str(path),arcname=relative)
                info.uid=info.gid=0;info.uname=info.gname=''
                with path.open('rb') as stream:
                    reader=HashedReader(stream);archive.addfile(info,reader)
                after=path.stat()
                assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Source changed: '+relative
                manifest['files'][relative]=dict(archive=name,bytes=info.size,sha256=reader.hash.hexdigest())
        manifest['archives'][name]=dict(bytes=target.stat().st_size,sha256=sha(target),files=len(paths))
        print(name,len(paths),'files;',target.stat().st_size,'compressed bytes',flush=True)
    (output/'checkpoint-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Checkpoint complete:',len(manifest['files']),'files',flush=True)


if __name__=='__main__':main()
