# Assembly Language

*This documentation is still in progress...*

- [Instruction overview](#instruction-overview)
- [Example code](#example-code)
- [Addressing modes](#addressing-modes)
- [Value formats](#value-formats)
- [Memory layout](#memory-layout)
- [Instruction reference](#instruction-reference)

<a name="instruction-overview"></a>
## Instruction overview

The table below briefly describes the instructions that are support by the DM-02 assembly language. Each of the instructions is described in more detail in this document.

| Mnemonic                     | Description                                                  |
| ---------------------------- | ------------------------------------------------------------ |
| [MOV](#MOV)                  | Transfer data from one location (e.g. register or memory location) to another. |
| [PUSH](#PUSH)                | Push data onto the stack                                     |
| [POP](#POP)                  | Pop data from the stack                                      |
| [ADD](#ADD)                  | Add to accumulator                                           |
| [ADC](#ADC)                  | Add to accumulator with carry                                |
| [SUB](#SUB)                  | Subtract from accumulator                                    |
| [SBC](#SBC)                  | Subtract from accumulator with borrow                        |
| [INC](#INC)                  | Increment by one                                             |
| [DEC](#DEC)                  | Decrement by one                                             |
| [AND](#AND)                  | Logical AND with accumulator                                 |
| [OR](#OR)                    | Logical OR with accumulator                                  |
| [XOR](#XOR)                  | Logical XOR with accumulator                                 |
| [NOT](#NOT)                  | Invert value                                                 |
| [SHL](#SHL)                  | Shift bits to the left                                       |
| [SHR](#SHR)                  | Shift bits to the right                                      |
| [ROL](#ROL)                  | Rotate (carry-over) bits to the left                         |
| [ROR](#ROR)                  | Rotate (carry-over) bits to the right                        |
| [CMP](#CMP)                  | Compare with accumulator (performs subtraction, but only affect flags) |
| [JMP](#JMP)                  | Jump program counter to address                              |
| [JMP](#JMPc) (conditional)   | Jump program counter to address if certain condition (flag) applies |
| [CALL](#CALL)                | Call a subroutine                                            |
| [CALL](#CALLc) (conditional) | Call a subroutine if certain condition (flag) applies        |
| [RET](#RET)                  | Return from subroutine                                       |
| [RET](#RETc) (conditional)   | Return from subroutine if certain condition (flag) applies   |
| [FSET](#FSET)                | Flag set                                                     |
| [FCLR](#FCLR)                | Flag clear                                                   |
| [NOP](#NOP)                  | No operation (do nothing)                                    |
| [HALT](#HALT)                | Halt program execution                                       |
| SP                           | *Initialize stack pointer*                                   |



<a name="example-code"></a>
## Example code
```
.data
message   : "Hello world"                  ; Store string data (terminated with 0).
bytes     : $A4 $FF $5B ‘G’ 128 %10010011  ; Store multiple bytes of data.
            $FF $4A $DE
$4F00     : $00 $01 $02 $03 $04            ; Store data at explicit address.
serialout = $FF00                          ; Define an address pointer.

.code   
main:   MOV HL,message  ; Load 16-bit address to message string into HL register pair.
        MOV B,#0        ; Load immediate value 0 into B.

nxtchr: MOV A,(HL)      ; Transfer value from memory location HL into A.
        CMP B           ; Compare A and B.
        JZ done         ; If A-B=0, we hit the end of our string.
        MOV serialout,A ; Transfer value from A to $FF00 (I/O address).

        INC HL          ; Increment value of the HL register pair.
        JMP nxtchr      ; Repeat for the next character in the string.

done:   HALT
```



<a name="address-modes"></a>
## Addressing modes

Where DM-01 had many different mnemonics for data transfer, DM-02 mainly uses the `MOV` instruction combined with different addressing modes.

Here are some examples of DM-01 instructions and how they are expressed in the DM-02 assembly language:

| DM-01 instruction | DM-02 instruction |
| ----------------- | ----------------- |
| `MOV A B`         | `MOV A,B`         |
| `MVI A 0xF8`      | `MOV A,#$F8`      |
| `LD A 0xBF46`     | `MOV A,$BF46`     |
| `ST A 0xBF46`     | `MOV $BF46,A`     |
| `LDX A 0xBF46`    | `MOV A,($BF46)`   |
| `LDR A`           | `MOV A,(HL)`      |

**The DM-02 supports the following explicit addressing modes:**

| Mode              | Example notation         | Description                                                  |
| ----------------- | ------------------------ | ------------------------------------------------------------ |
| Absolute register | A                        | Refers to a register to get data from or write data to       |
| Immediate value   | #$FF                     | Defines immediate data                                       |
| Absolute address  | $FA6C                    | Defines a memory address to get data from or write data to   |
| Indirect address  | ($FA6C)                  | Defines a memory address, that contains the memory address to get data from or write data to |
| Indirect register | (HL)                     | Refers to a register pair, that contains the memory address to get data from or write data to |
| *Indexed modes*   | *$B47E+A<br>($B47E+A)*   | _**Currently not supported**, but may be implemented in the future_ |


<a name="value-formats"></a>
## Value formats

Values for data or addresses may be expressed using different formats:

| Value Type  | Format    | Example                |
| ----------- | --------- | ---------------------- |
| decimal     | *value*   | `MOV A,#65`            |
| hexadecimal | $*value*  | `MOV A,#$41`           |
| binary      | %*value*  | `MOV A,%1000001`       |
| character   | '*value*' | `MOV A,#'A'`           |
| string      | "*value*" | `$4F00: "Hello world"` |


<a name="memory-layout"></a>
## Memory layout

| Start address | End address | Description |
| ------------- | ----------- | ----------- |
| 0000          | 3FFF        | ROM         |
| 4000          | FEFF        | RAM         |
| FEFF          | 4000        | Stack space |
| FF00          | FFFF        | I/O         |



- No zero-page addressing support (may be added in future)
- *Assembler must know memory offset (wether it runs from ROM or RAM)*
- Stack space starts at the end of RAM and works its way back to the start when data is pushed onto it.
- The entire RAM may be used for stack.
- *MAR can increment by one - used when loading 16-bit data* 


<a name="instruction-reference"></a>
## Instruction reference

<a name="MOV"></a>

### MOV

|                                           |
| ----------------------------------------- |
| MOV A,B                                   |
| MOV A,C                                   |
| MOV A,H                                   |
| MOV A,L                                   |
| MOV B,A                                   |
| MOV B,C                                   |
| MOV B,H                                   |
| MOV B,L                                   |
| MOV C,A                                   |
| MOV C,B                                   |
| MOV C,H                                   |
| MOV C,L                                   |
| MOV H,A                                   |
| MOV H,B                                   |
| MOV H,C                                   |
| MOV H,L                                   |
| MOV L,A                                   |
| MOV L,B                                   |
| MOV L,C                                   |
| MOV L,H                                   |
| MOV   BC,HL                               |
| MOV   HL,BC                               |
| MOV   A,#$value                           |
| MOV   B,#$value                           |
| MOV   C,#$value                           |
| MOV   H,#$value                           |
| MOV   L,#$value                           |
| MOV   BC,#$value                          |
| MOV   HL,#$value                          |
| MOV   A,$address                          |
| MOV   B,$address                          |
| MOV   C,$address                          |
| MOV   BC,$address                         |
| MOV   HL,$address                         |
| MOV   $address,A                          |
| MOV   $address,B                          |
| MOV   $address,C                          |
| MOV   $address,BC                         |
| *MOV   $address,HL* <<<<< NOT IMPLEMENTED |
| MOV   A,($address)                        |
| MOV   B,($address)                        |
| MOV   C,($address)                        |
| MOV   BC,($address)                       |
| MOV   ($address),A                        |
| MOV   ($address),B                        |
| MOV   ($address),C                        |
| MOV   ($address),BC                       |
| MOV   A,(BC)                              |
| MOV   H,(BC)                              |
| MOV   L,(BC)                              |
| MOV A,(HL)                                |
| MOV B,(HL)                                |
| MOV C,(HL)                                |
| MOV   (BC),A                              |
| MOV   (BC),H                              |
| MOV   (BC),L                              |
| MOV (HL),A                                |
| MOV (HL),B                                |
| MOV (HL),C                                |

<a name="PUSH"></a>
### PUSH

|         |
| ------- |
| PUSH A  |
| PUSH B  |
| PUSH C  |
| PUSH H  |
| PUSH L  |
| PUSH BC |
| PUSH HL |
| PUSH F  |

<a name="POP"></a>
### POP

|        |
| ------ |
| POP A  |
| POP B  |
| POP C  |
| POP H  |
| POP L  |
| POP BC |
| POP HL |
| POP F  |

<a name="ADD"></a>
### ADD

|                  |
| ---------------- |
| ADD A            |
| ADD B            |
| ADD C            |
| ADD H            |
| ADD L            |
| *ADD #$value*    |
| *ADD $address*   |
| *ADD ($address)* |
| *ADD (HL)*       |

<a name="ADC"></a>
### ADC

|                  |
| ---------------- |
| ADC A            |
| ADC B            |
| ADC C            |
| ADC H            |
| ADC L            |
| *ADC #$value*    |
| *ADC $address*   |
| *ADC ($address)* |
| *ADC (HL)*       |

<a name="SUB"></a>
### SUB

|                  |
| ---------------- |
| SUB A            |
| SUB B            |
| SUB C            |
| SUB H            |
| SUB L            |
| *SUB #$value*    |
| *SUB $address*   |
| *SUB ($address)* |
| *SUB (HL)*       |

<a name="SBC"></a>
### SBC

|                  |
| ---------------- |
| SBC A            |
| SBC B            |
| SBC C            |
| SBC H            |
| SBC L            |
| *SBC #$value*    |
| *SBC $address*   |
| *SBC ($address)* |
| *SBC (HL)*       |

<a name="INC"></a>
### INC

|          |
| -------- |
| INC A    |
| *INC B*  |
| *INC C*  |
| *INC H*  |
| *INC L*  |
| *INC BC* |
| *INC HL* |

<a name="DEC"></a>
### DEC

|          |
| -------- |
| DEC A    |
| *DEC B*  |
| *DEC C*  |
| *DEC H*  |
| *DEC L*  |
| *DEC BC* |
| *DEC HL* |

<a name="AND"></a>
### AND

|                  |
| ---------------- |
| AND B            |
| AND C            |
| AND H            |
| AND L            |
| *AND #$value*    |
| *AND $address*   |
| *AND ($address)* |
| *AND (HL)*       |

<a name="OR"></a>
### OR

|                 |
| --------------- |
| OR B            |
| OR C            |
| OR H            |
| OR L            |
| *OR #$value*    |
| *OR $address*   |
| *OR ($address)* |
| *OR (HL)*       |

<a name="XOR"></a>
### XOR

|                  |
| ---------------- |
| XOR B            |
| XOR C            |
| XOR H            |
| XOR L            |
| *XOR #$value*    |
| *XOR $address*   |
| *XOR ($address)* |
| *XOR (HL)*       |

<a name="NOT"></a>
### NOT

|                  |
| ---------------- |
| NOT A            |
| NOT B            |
| NOT C            |
| NOT H            |
| NOT L            |
| *NOT #$value*    |
| *NOT $address*   |
| *NOT ($address)* |
| *NOT (HL)*       |

<a name="SHL"></a>

### SHL

|                  |
| ---------------- |
| SHL A            |
| SHL B            |
| SHL C            |
| SHL H            |
| SHL L            |
| *SHL #$value*    |
| *SHL $address*   |
| *SHL ($address)* |
| *SHL (HL)*       |

<a name="SHR"></a>
### SHR

|                  |
| ---------------- |
| SHR A            |
| SHR B            |
| SHR C            |
| SHR H            |
| SHR L            |
| *SHR #$value*    |
| *SHR $address*   |
| *SHR ($address)* |
| *SHR (HL)*       |

<a name="ROL"></a>
### ROL

|                  |
| ---------------- |
| ROL A            |
| ROL B            |
| ROL C            |
| ROL H            |
| ROL L            |
| *ROL #$value*    |
| *ROL $address*   |
| *ROL ($address)* |
| *ROL (HL)*       |

<a name="ROR"></a>
### ROR

|                  |
| ---------------- |
| ROR A            |
| ROR B            |
| ROR C            |
| ROR H            |
| ROR L            |
| *ROR #$value*    |
| *ROR $address*   |
| *ROR ($address)* |
| *ROR (HL)*       |

<a name="CMP"></a>
### CMP

|                  |
| ---------------- |
| CMP B            |
| CMP C            |
| CMP H            |
| CMP L            |
| *CMP #$value*    |
| *CMP $address*   |
| *CMP ($address)* |
| *CMP (HL)*       |

<a name="JMP"></a>
### JMP

<a name="JMPc"></a>

### JMP (conditional)

|               |
| ------------- |
| JC   $address |
| JZ $address   |
| JN $address   |
| JO $address   |
| JNC $address  |
| JNZ $address  |
| JP $address   |
| JNO $address  |

<a name="CALL"></a>
### CALL

<a name="CALLc"></a>

### CALL (conditional)

|              |
| ------------ |
| CC $address  |
| CZ $address  |
| CN $address  |
| CO $address  |
| CNC $address |
| CNZ $address |
| CP $address  |
| CNO $address |

<a name="RET"></a>
### RET

<a name="RETc"></a>

### RET (conditional)

|      |
| ---- |
| RC   |
| RZ   |
| RN   |
| RO   |
| RNC  |
| RNZ  |
| RP   |
| RNO  |

<a name="FSET"></a>
### FSET

|        |
| ------ |
| FSET C |
| FSET Z |

<a name="FCLR"></a>
### FCLR

|        |
| ------ |
| FCLR C |
| FCLR Z |

<a name="NOP"></a>
### NOP

<a name="HALT"></a>

### HALT