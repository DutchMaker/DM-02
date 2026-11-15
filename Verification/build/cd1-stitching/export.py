"""Run the archived KiCad geometry exporter for P2 in this experiment."""
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native_export', HERE / 'sources/export_geometry.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROOT = HERE.parents[2]
sys.argv = [__file__, '--source', str(HERE), '--out', str(HERE), '--board', 'CD1-P2-routed.kicad_pcb']
module.main()
