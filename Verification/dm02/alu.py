"""Independent mathematical oracle; V is zero outside signed arithmetic."""
import struct
from .common import ROOT, BUILD, command, evidence, write_json

NAMES=['ZERO','A','B','NEG A','NEG B','INC A','INC B','DEC A','DEC B',
       'ADD','ADC','SUB','SUB special','B-A','SBC','B-A-1','MUL low','MUL high',
       'DIV','MOD','SHL','SHR','ASR','ROL','ROR','AND','OR','XOR','NOT A','NOT B','BCD ADD','BCD SUB']


def signed(n):
    return n if n<128 else n-256


def decimal(n):
    return (n//16 if n//16<10 else 0)*10+(n%16 if n%16<10 else 0)


def expected(op,a,b):
    sa,sb=signed(a),signed(b)
    carry=0
    overflow=0
    if op<16:
        raw=[0,a,b,-a,-b,a+1,b+1,a-1,b-1,a+b,a+b+1,a-b,a-b,b-a,a-b-1,b-a-1][op]
        sr=[0,sa,sb,-sa,-sb,sa+1,sb+1,sa-1,sb-1,sa+sb,sa+sb+1,sa-sb,sa-sb,sb-sa,sa-sb-1,sb-sa-1][op]
        overflow=int(not -128<=sr<=127)
        carry=int(raw<0 or raw>255)
        value=raw%256
    elif op==16: value=a*b%256
    elif op==17: value=a*b//256
    elif op==18: value=a//b if b else 0
    elif op==19: value=a%b if b else 0
    elif op==20:
        raw=a*2**b
        value=raw%256
        carry=(raw//256)%2
    elif op==21: value=a//2**b
    elif op==22: value=(sa//2**b)%256
    elif op==23:
        n=b%8; value=((a<<n)|(a>>(8-n)))%256
    elif op==24:
        n=b%8; value=((a>>n)|(a<<(8-n)))%256
    elif op==25: value=a&b
    elif op==26: value=a|b
    elif op==27: value=a^b
    elif op==28: value=255-a
    elif op==29: value=255-b
    else:
        raw=decimal(a)+(decimal(b) if op==30 else -decimal(b))
        carry=int(raw<0 or raw>=100)
        n=raw%100; value=(n//10)*16+n%10
    zero=int(value==0) ^ int(op==12)
    return value | carry<<8 | overflow<<9 | zero<<10 | int(value>=128)<<11 | int(op in (18,19) and b==0)<<12


def run():
    folder=BUILD/'alu'
    folder.mkdir(parents=True,exist_ok=True)
    code,log=command(['perl',ROOT/'Code/ALU/generate_alu.pl'],cwd=folder,timeout=180)
    (folder/'generate.log').write_text(log)
    if code: raise RuntimeError(log)
    banks=[(folder/f'alu{i}.rom').read_bytes() for i in range(8)]
    if any(len(b)!=524288 for b in banks): raise ValueError('ALU bank length mismatch')
    words=struct.unpack('<2097152H',b''.join(banks))
    rows=[]
    for op,name in enumerate(NAMES):
        data_errors=flag_errors=core_errors=0; examples=[]; data_examples=[]
        for a in range(256):
            for b in range(256):
                address=(op<<16)|(a<<8)|b
                actual=words[address]; want=expected(op,a,b)
                data_errors+=int((actual&255)!=(want&255))
                flag_errors+=int((actual>>8)!=(want>>8))
                mask=0xffff
                core_errors+=int(bool((actual^want)&mask))
                if actual!=want and len(examples)<4:
                    examples.append(dict(address=address,a=a,b=b,actual=f'{actual:04x}',expected=f'{want:04x}'))
                if (actual&255)!=(want&255) and len(data_examples)<4:
                    data_examples.append(dict(address=address,a=f'{a:02x}',b=f'{b:02x}',actual=f'{actual&255:02x}',expected=f'{want&255:02x}'))
        rows.append(dict(op=op,name=name,checked=65536,data_errors=data_errors,flag_errors=flag_errors,core_errors=core_errors,examples=examples,data_examples=data_examples))
    total=sum(r['data_errors'] for r in rows)
    flags=sum(r['flag_errors'] for r in rows)
    core=sum(r['core_errors'] for r in rows)
    write_json(folder/'exhaustive.json',dict(checked=len(words),data_errors=total,flag_errors=flags,operations=rows,
        contract='Generator opcode order; modulo-256 arithmetic, modulo-100 BCD, borrow carry, special op12 Z inversion. Signed overflow for opcodes 3–15; V=0 for every other operation.',
        core_errors=core,
        specification_conflicts=[]))
    return [evidence('alu','Exhaustive ALU ROM audit','fail' if total or flags else 'pass',
                    f'{len(words):,} words checked: {total:,} data mismatches; {flags:,} flag-contract mismatches.',
                    rows=rows,checked=len(words),artifacts=['alu/exhaustive.json','alu/generate.log'],
                    limitation='Complete ROM data contract; electrical ROM interface and flag capture are separate checks.'),
            evidence('alu-core','ALU data and specified arithmetic flags','pass' if core==0 else 'fail',
                     f'{len(words):,} words checked; {total:,} data mismatches; {core:,} mismatches in checked data/flag bits.',
                     artifacts=['alu/exhaustive.json'],limitation='All word bits checked, including C, V, Z, N, divide-by-zero and unused output bits for every word.')]
