from datetime import datetime, timezone
from .common import ROOT, VROOT, BUILD, digest


def sources():
    paths=[]
    ignored={'build','bin','obj','node_modules','.venv','__pycache__','.DS_Store'}
    for directory in ('Verification','Circuits','Code','Documentation','Logisim'):
        for path in (ROOT/directory).rglob('*'):
            if path.is_file() and not any(p in ignored for p in path.relative_to(ROOT).parts) and path.suffix not in ('.pyc','.tmp'):
                paths.append(path)
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}


def freshness(report, current=None):
    current=sources() if current is None else current
    old=report.get('source_hashes',{})
    changes=sorted(p for p in old.keys()|current.keys() if old.get(p)!=current.get(p))
    return dict(fresh=bool(old) and not changes and report.get('state')=='complete',changed=changes,
                state=report.get('state','missing'))


def now():
    return datetime.now(timezone.utc).isoformat()


def trace(requirements, checks):
    by_id={c['id']:c for c in checks}
    return [dict(r,status=by_id.get(r['gate'],{}).get('requirement_status',by_id.get(r['gate'],{}).get('status','blocked'))) for r in requirements['requirements']]


def milestones(requirements,checks):
    by_id={r['id']:r for r in trace(requirements,checks)}; rows=[]
    for milestone in requirements['milestones']:
        gates=[by_id[r] for r in milestone['requirements']]
        if not gates: raise ValueError('A milestone must have acceptance requirements')
        outstanding=[r for r in gates if r['status']!='pass']
        status='complete' if not outstanding else next((s for s in ('error','blocked','fail','limited') if any(r['status']==s for r in outstanding)),'in progress')
        passed=len(gates)-len(outstanding)
        rows.append(dict(milestone,status=status,passed=passed,total=len(gates),gates=gates,
                         summary=f'{passed}/{len(gates)} acceptance gates passed.'+
                         (' Open: '+', '.join(r['id'] for r in outstanding)+'.' if outstanding else '')))
    return rows
