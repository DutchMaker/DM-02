"""Independent source expansion/encoding and compiled-ROM audit.

The Python path does not import compiler classes or extract expected words from
the C# output. Encodings follow the documented 16-bit word/address layout.
"""
import re
import struct
from pathlib import Path
from .common import ROOT, BUILD, command, evidence, write_json, digest

FLAGS={'C':0,'O':1,'Z':2,'N':3}
REGISTERS='A B C H L'.split()


def encode(lines, tables):
    operands,functions,alu=tables
    text=' '.join(lines)
    data=text.startswith('[data]')
    selected=re.search(r'^\[data\]\[([^]]+)\]',text)
    operation=selected[1] if selected else None
    tokens=re.sub(r'\[[^]]*\]','',text).split()
    out=load=0; controls=[]
    for token in tokens:
        if token.isdigit(): continue  # Optional source t-state number.
        if token in functions: controls.append(functions[token])
        elif token.endswith(('_out','_load')):
            name,direction=token.rsplit('_',1)
            if name not in operands: raise ValueError(f'Unknown operand {token}')
            if direction=='out':
                if out: raise ValueError('Multiple bus outputs in one control word')
                out=operands[name]
            else:
                if load: raise ValueError('Multiple bus loads in one control word')
                load=operands[name]
        else: raise ValueError(f'Unknown control token {token}')
    if not data:
        if out or load or operation: raise ValueError('Operands in function word')
        if len(controls)>2: raise ValueError('Too many function controls')
        return (controls[0]<<11 if controls else 0)|(controls[1]<<1 if len(controls)>1 else 0)
    if operation:
        if operation not in alu: raise ValueError(f'Unknown ALU function {operation}')
        if controls: raise ValueError('Function controls cannot fit in ALU word')
        tail=0x40|(alu[operation]<<1)
    else:
        if len(controls)>1: raise ValueError('Too many controls in data word')
        tail=controls[0]<<1 if controls else 0
    return 0x8000|(out<<11)|(load<<7)|tail


def reference(text):
    lines=[line.split('#',1)[0].strip() for line in text.splitlines()]
    lines=[line for line in lines if line]
    def section(name):
        start=lines.index(name)+1; end=lines.index('.end',start)
        return lines[start:end]
    tables=[]
    for name,width in [('.operands',4),('.functions',4),('.alu',5)]:
        values={}
        for line in section(name):
            bits,key=line.split(':',1)
            if not re.fullmatch('[01]{'+str(width)+'}',bits): raise ValueError('Invalid encoding width')
            if key in values or int(bits,2) in values.values(): raise ValueError('Duplicate bit pattern')
            values[key]=int(bits,2)
        tables.append(values)
    instructions={}
    for line in section('.instructions'):
        op,size,mnemonic=line.split(':',2)
        op=int(op,16)
        if op in instructions: raise ValueError('Duplicate instruction')
        instructions[op]=dict(name=mnemonic,size=int(size))
    words=[0]*65536; assigned={}; sequences={}; by_name={}
    cursor=lines.index('.code')+1
    while cursor<len(lines) and lines[cursor]!='.end':
        header=lines[cursor]; end=lines.index('.end',cursor+1)
        body=lines[cursor+1:end]; cursor=end+1
        condition=re.search(r'\s*\[([COZN])=([01])\]$',header)
        condition_bits=(FLAGS[condition[1]],int(condition[2])) if condition else None
        template=header[:condition.start()] if condition else header
        pattern=re.escape(template)
        for token,options in [('hl1','BC|HL'),('hl2','BC|HL'),('r1','A|B|C|H|L'),('r2','A|B|C|H|L')]:
            pattern=pattern.replace(token,f'(?P<{token}>{options})')
        matched=False
        for op,ins in instructions.items():
            match=re.fullmatch(pattern,ins['name'])
            if not match: continue
            matched=True; replacements=match.groupdict()
            for suffix in ('1','2'):
                pair=replacements.get('hl'+suffix)
                if pair: replacements.update({'h'+suffix:pair[0],'l'+suffix:pair[1]})
            expanded=[re.sub(r'(?<![A-Za-z0-9])(hl[12]|r[12]|h[12]|l[12])(?![A-Za-z0-9])',lambda m:replacements[m[1]],line) for line in body]
            if expanded and expanded[0].startswith('>'):
                sequence=by_name[expanded[0][1:].strip()]
            else:
                states=[]
                for line in expanded:
                    if line.startswith(':'): states.append([line[1:].strip()])
                    elif states: states[-1].append(line)
                    else: raise ValueError(f'Control before t-state: {header}')
                if not 1<=len(states)<=16: raise ValueError(f'Invalid t-state count: {header}')
                try: sequence=[encode(state,tables) for state in states]
                except ValueError as err: raise ValueError(f'{header}: {err}') from err
            by_name.setdefault(ins['name'],sequence)
            for flags in range(16):
                if condition_bits and (flags>>condition_bits[0])&1 != condition_bits[1]: continue
                if (op,flags) in sequences: raise ValueError(f'Duplicate sequence: {ins["name"]}, flags={flags}')
                sequences[op,flags]=sequence
                for t,word in enumerate(sequence):
                    address=(op<<8)|(t<<4)|flags
                    if address in assigned: raise ValueError('Overlapping ROM address')
                    assigned[address]=dict(op=op,t=t,flags=flags)
                    words[address]=word
        if not matched: raise ValueError(f'Unmatched instruction template: {template}')
    missing=[(op,f) for op in instructions for f in range(16) if (op,f) not in sequences]
    if missing: raise ValueError(f'Missing instruction/flag definitions: {missing[:10]}')
    return dict(words=words,assigned=assigned,sequences=sequences,instructions=instructions,tables=tables)


def run():
    folder=BUILD/'microcode'; folder.mkdir(parents=True,exist_ok=True)
    source=ROOT/'Code/Microcode/microcode.src'
    spec=reference(source.read_text())
    code,log=command(['dotnet','build',ROOT/'Code/Microcode/src/Mcc/Mcc.csproj','--no-restore'],timeout=120)
    (folder/'build.log').write_text(log)
    if code: raise RuntimeError(log)
    dll=ROOT/'Code/Microcode/src/Mcc/bin/Debug/netcoreapp2.2/mcc.dll'
    staged=folder/'microcode.src'; staged.write_text(source.read_text())
    for suffix in ('.rom','.img'): staged.with_suffix(suffix).unlink(missing_ok=True)
    code,log=command(['dotnet','--roll-forward','Major',dll,staged])
    (folder/'compile.log').write_text(log)
    if code: raise RuntimeError(log)
    binary=staged.with_suffix('.rom').read_bytes()
    tokens=staged.with_suffix('.img').read_text().split()
    if tokens[:2]!=['v2.0','raw']: raise ValueError('Invalid Logisim header')
    image=[int(t,16) for t in tokens[2:]]
    actual=list(struct.unpack('<'+str(len(binary)//2)+'H',binary))
    errors=[dict(address=i,expected=w,binary=actual[i] if i<len(actual) else None,
                 logisim=image[i] if i<len(image) else None) for i,w in enumerate(spec['words'])
            if i>=len(actual) or i>=len(image) or w!=actual[i] or w!=image[i]]
    copies={suffix:digest(source.with_suffix(suffix))==digest(staged.with_suffix(suffix)) for suffix in ('.rom','.img')}
    lengths=[len(sequence) for sequence in spec['sequences'].values()]
    result=dict(binary_words=len(actual),logisim_words=len(image),expected_words=65536,
                assigned_words=len(spec['assigned']),unused_words=65536-len(spec['assigned']),
                instructions=len(spec['instructions']),instruction_flag_sequences=len(lengths),
                longest_sequence=max(lengths),differences=len(errors),examples=errors[:12],committed_copies_match=copies,
                fill_policy='Unassigned words are zero. This preserves prior internal-gap semantics; invalid opcodes are not fail-stop.',
                source_sha256=digest(source),compiler_sha256=digest(dll))
    write_json(folder/'rom-audit.json',result)
    write_json(folder/'sequences.json',[dict(op=op,name=spec['instructions'][op]['name'],flags=flags,words=[f'{w:04x}' for w in seq]) for (op,flags),seq in spec['sequences'].items()])
    ok=len(actual)==len(image)==65536 and not errors and all(copies.values())
    return evidence('microcode','Independent microcode ROM audit','pass' if ok else 'fail',
                    f'{len(lengths):,} opcode/flag sequences; {len(errors):,} word mismatches; binary {len(actual):,}, Logisim {len(image):,} words.',
                    audit=result,artifacts=['microcode/rom-audit.json','microcode/sequences.json','microcode/compile.log'],
                    limitation='Independent source expansion and encoding, not timed hardware execution. Zero-fill is a storage policy; unused-opcode behaviour still needs a hardware decision.')
