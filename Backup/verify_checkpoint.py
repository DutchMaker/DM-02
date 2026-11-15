"""Verify downloaded evidence archives and every member without extracting."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    args=parser.parse_args();root=args.directory
    manifest=json.loads((root/'checkpoint-manifest.json').read_text())
    seen=set()
    for name,expected in manifest['archives'].items():
        assert Path(name).name==name
        path=root/name;assert path.stat().st_size==expected['bytes']
        with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==expected['sha256'],name
        count=0
        with tarfile.open(path,'r|gz') as archive:
            for member in archive:
                parts=PurePosixPath(member.name)
                assert member.isfile() and not parts.is_absolute() and '..' not in parts.parts
                assert member.name not in seen and member.name in manifest['files'],member.name
                row=manifest['files'][member.name]
                assert row['archive']==name and member.size==row['bytes'],member.name
                with archive.extractfile(member) as stream:
                    digest=hashlib.file_digest(stream,'sha256').hexdigest()
                assert digest==row['sha256'],member.name
                seen.add(member.name);count+=1
        assert count==expected['files'];print(name,count,'files verified',flush=True)
    assert seen==set(manifest['files'])
    print('All',len(seen),'files match the checkpoint manifest for',manifest['git_commit'],flush=True)


if __name__=='__main__':main()
