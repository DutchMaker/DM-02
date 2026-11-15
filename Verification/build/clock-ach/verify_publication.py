"""Check every ACH artifact through the existing remote dashboard."""
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('verify',HERE.parent/'cd1-electrical/verify_publication.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.HERE=HERE
module.BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/clock-ach/'
module.main()
