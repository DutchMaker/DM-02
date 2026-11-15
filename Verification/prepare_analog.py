"""Download pinned original models/checker into a user-supplied private cache."""
import argparse
import hashlib
import io
from pathlib import Path
import subprocess
import urllib.request
import zipfile
from dm02.ibis_driver import MODEL_HASH, CHECKER_SHA1
from dm02.loaded_output import cache_directory, require_private


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cache', type=Path, nargs='?')
    args = parser.parse_args()
    args.cache=require_private(args.cache.expanduser()) if args.cache else cache_directory()
    args.cache.mkdir(parents=True, exist_ok=True)
    model = args.cache/'sclm097a.ibs'
    require_private(model)
    if not model.exists():
        data = urllib.request.urlopen('https://www.ti.com/lit/ibs/SCLM097', timeout=60).read()
        assert hashlib.sha256(data).hexdigest() == MODEL_HASH, 'Manufacturer download changed; review required'
        model.write_bytes(data)
    assert hashlib.sha256(model.read_bytes()).hexdigest() == MODEL_HASH
    checker = args.cache/'ibischk7_64'
    license_file = args.cache/'IBIS_Binary_Code_License.txt'
    require_private(checker)
    require_private(license_file)
    if not checker.exists() or not license_file.exists():
        # This host rejects urllib's request (HTTP 406); curl succeeds.
        data = subprocess.run(['curl', '-fsSL', '--max-time', '60',
            'https://www.ibis.org/ibischk7/ibischk721_maca_64.zip'], check=True, capture_output=True).stdout
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            executable = archive.read('ibischk721_maca_64/ibischk7_64')
            assert hashlib.sha1(executable).hexdigest() == CHECKER_SHA1
            license_file.write_bytes(archive.read('ibischk721_maca_64/IBIS_Binary_Code_License.txt'))
            checker.write_bytes(executable)
    assert hashlib.sha1(checker.read_bytes()).hexdigest() == CHECKER_SHA1
    checker.chmod(0o755)
    print('Verified original TI model and official Apple-silicon IBISCHK 7.2.1 in', args.cache)


if __name__ == '__main__':
    main()
