"""Use the preserved artifact verifier against the new publication."""
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('published_verifier', HERE.parent / 'cd1-electrical/verify_publication.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.HERE = HERE
module.BASE = 'https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cd1-stitching/'
module.main()
