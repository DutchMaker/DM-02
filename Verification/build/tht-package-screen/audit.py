"""Check exported part identities and exercise serialized-netlist fault cases."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.legacy import read_sheet,inventory,connectivity


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(tree,sheet):
    expected={p['ref']:(p['value'],p['footprint']) for p in inventory(sheet)['packages']}
    actual={p.attrib['ref']:(p.findtext('value'),p.findtext('footprint','')) for p in tree.findall('./components/comp')}
    assert expected==actual,'exported part/footprint identity'
    want={frozenset(tuple(n) for n in net['nodes']) for net in connectivity(sheet)}
    got={frozenset((n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')) for net in tree.findall('./nets/net')}
    assert want==got,'exported pin-group identity'
    return len(expected),len(want)


def main():
    summary=json.loads((HERE/'summary.json').read_text());rows=[];inputs={}
    for board in summary['boards']:
        source=ROOT/board['source'];assert sha(source)==board['source_sha256']
        candidate=HERE/board['candidate'];assert sha(candidate)==board['candidate_sha256']
        original=read_sheet(source);sheet=read_sheet(candidate)
        inputs[board['source']]=board['source_sha256']
        for c in original['components']:inputs[c['library_source']]=sha(ROOT/c['library_source'])
        xml=HERE/'native'/board['board']/(sheet['name']+'.xml')
        parts,groups=verify(ET.parse(xml).getroot(),sheet)
        rows.append(dict(board=board['board'],parts=parts,net_groups=groups,passed=True,native_xml_sha256=sha(xml)))
    faults=[]
    sheet=read_sheet(HERE/'circuits/Data-PC1.sch')
    original=ET.parse(HERE/'native/PC1/Data-PC1.xml').getroot()
    folder=HERE/'faults';folder.mkdir(exist_ok=True)
    for name in ('soic-part-code-restored','soic-footprint-restored','counter-clock-pin-removed'):
        bad=copy.deepcopy(original);part=next(p for p in bad.findall('./components/comp') if p.attrib['ref']=='U1')
        if name=='soic-part-code-restored':part.find('value').text='CD74HCT161M96'
        elif name=='soic-footprint-restored':part.find('footprint').text='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm'
        else:
            matches=[(net,n) for net in bad.findall('./nets/net') for n in net.findall('node') if n.attrib['ref']=='U1' and n.attrib['pin']=='2']
            assert len(matches)==1
            matches[0][0].remove(matches[0][1])
        path=folder/(name+'.xml');ET.ElementTree(bad).write(path,encoding='utf-8',xml_declaration=True)
        try:verify(ET.parse(path).getroot(),sheet)
        except AssertionError as error:faults.append(dict(fault=name,detected=True,diagnostic=str(error),sha256=sha(path)))
        else:raise AssertionError('Serialized fault escaped '+name)
    archived=[]
    for source,digest in sorted(inputs.items()):
        dest=HERE/'sources/original'/source;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/source,dest);assert sha(dest)==digest
        archived.append(dict(source=source,sha256=digest,file=str(dest.relative_to(HERE))))
    result=dict(passed=True,boards=rows,parts_verified=sum(r['parts'] for r in rows),net_groups_verified=sum(r['net_groups'] for r in rows),
        changed_package_pads=sum(r['pads'] for r in summary['changes']),faults=faults,original_inputs=archived,
        scope='Native XML part values, footprint properties and pin groups; three serialized faults. Pin-number coverage does not establish lead/hole tolerance or socket fit.')
    (HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['parts_verified'],'exported part identities;',result['net_groups_verified'],'net groups;',len(faults),'serialized faults rejected')


if __name__=='__main__':main()
