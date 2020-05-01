# Assembly Language

*This documentation is still in progress...*

- [Instruction overview](#instruction-overview)
- [Example code](#example-code)
- [Source file structure](#source-file-structure)
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
| [SP](#SP)                    | Initialize stack pointer                                     |
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
| [SHL](#SHL)                  | Logical shift left                                           |
| [SHR](#SHR)                  | Logical shift right                                          |
| [ASR](#ASR)                  | Arithmetic shift right                                       |
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



<a name="example-code"></a>

## Example code

The following piece of example code demonstrates all of the features supported by the assembler (except for every possible instruction).

```
.data																; Data is always stored at the start of memory.
message   : "Hello World"           ; Store string data (automatically terminated with $00).

multiline : "This uses multiple " _ ; An _ is required when a string definition spans
            "lines to define data"  ; multiple lines so the assembler knows to terminate.
            
bytes     : $A4 $FF $5B 'G'         ; Store multiple bytes of data.
            $BC 65 %10001001 $AA    ; data may continue on the next line.
            $AA $BB 
            
buffer    : [1024]                  ; Only define a pointer and reserve space 
                                    ; without predefining the data.
            
*txt_out  : $FF00                   ; Define an address pointer.
                                    ; The * prefix tells the assembler not to apply the 
                                    ; memory offset.
                                    
~maxbyte  : #$FF                    ; Define a constant (simply replaced by the assembler)
~zero     : #0

.include  "example_data.asm"        ; Include the contents of another file.
.offset		$4000											; Define the memory offset (depends on wether the
                                    ; program will run from ROM or RAM).

.code
main:							; The program starts at the 'main' label.
  MOV BC,#message ; Load 16-bit address to the 'message' string into BC register pair.
          
nextchar: 
  MOV A,(BC)      ; Transfer value from memory location HL into A.

  ; Check if we reached the end of the string:
  CMP ~zero       ; Compare A to 0.
  JZ done         ; If A==0 then we reached the string terminator.

  MOV *txt_out,A  ; Transfer value from A to $FF00 (I/O address).

  ; Incrementing a 16-bit register pair:
  INC C           ; First increment the lower byte value.
  MOV A,~zero     ; Load immediate value 0 into A.
  ADC B           ; Add A to B with carry, 
                  ; this increments the higher byte if needed.
  MOV B,A         ; Transfer A to B.
  
  JMP nextchar

done:     
  HALT


.data
example:  "Data may also be stored after the .code block" _
          "Special characters in strings are expressed by their hexadecimal code" _
          "This is a carriage return \0D and this is a tab \09"
```



<a name="source-file-structure"></a>

## Source file structure

Source files must contain one or more blocks of code and may optionally contain one of more data blocks. It may also define a memory offset, which is required if the program needs to execute from RAM:

```
.offset $4000		; memory starts at address hex 4000

.data
  ; this is a data block.
  ; it ends at the next block or end of file...
 
.code
  ; this is the code block (at least one block required)
  ; it ends at the next data block or end of file...
```

### Data blocks

Data blocks are used to predefine data and (at the same time) define address pointer variables and define constants that are replaced by the assembler:

```
.data
pointer_1   : "This is a string " _
              "and we use multiple lines of code " _
              "to define it."

pointer_2   : $41 65 'A' %01000001

pointer_3   : [1024]

pointer_4   : $FF

*pointer_5  : $FF00

~constant_1 : #$FF 
```

The following applies to the example above:

- `pointer_1` stores the bytes contained in the [string](#strings) into memory and stores its location in the pointer.
  For the sake of example, let's say it was stored at address `$4000` (the offset).
  That means that wherever you use `pointer_1` in your code, it will be replaced by `$4000`.

  The length of the string is 64 characters, but the assembler will **automatically add a null terminator** at the end. Therefore it will take up 65 bytes of space!

- `pointer_2` does exactly the same, but it defined the data as explicit bytes. Note how each byte value is [expressed in a different way](#value-formats), but they all are the same value.
  Because the previous defined data took up 65 bytes, `pointer_2` points to `$4041`.

- `pointer_3` only defines a pointer and reserves 1024 bytes of space, but does not define any data. Because the previous defined data took up 5 bytes, `pointer_3` points to `$4046`.

- `pointer_4` is only here as an example to demonstrate what reservering space does. The previous definition (`pointer_3`) reserved 1024 bytes of space and therefore, `pointer_4` points to `$4446`.

- `*pointer_5` refers to the explicit address `$FF00`.

- `~constant_1` will simply be searched/replaced by the assembler. While it makes sense to use it for byte or address values, you could use it for anything - even instructions.

### Code blocks

Code blocks are used to indicate to the assembler that program code definition is about to start:

```
.code
main:					; label main
  MOV A,#$FF	; store 255 in A
  HALT				; halt the processor
```

There may be multiple code blocks defined and they will be processed by the assembler in order of occurrence. This applies when using `.include` to include other files that may contain code.

#### Main label

Programs must contain a `main` label to indicate where program execution starts. This is required because the assembler will add bootloader code at the start of memory that jumps to this label.

### Includes

Other source files may be included by the assembler by refering to their file name:

```
.include "filename.asm"
```

This will include **all** contents of the file at the exact location of the `.include` directive.

### Offset

Because programs may be executed from either ROM or RAM, the assembler needs to know where memory starts:

```
.offset $4000
```

This directive is optional and will default to address zero.

**Note:** the computer uses a 64 Kb RAM chip, but only the last 48 Kb can be addressed by the processor. Therefore RAM program storage starts at address `$4000`.

<a name="address-modes"></a>

## Addressing modes

Where DM-01 had many different mnemonics for data transfer, DM-02 mainly uses the `MOV` instruction combined with different addressing modes.

Here are some examples of DM-01 instructions and how they are expressed in the DM-02 assembly language:

| DM-01 instruction              | DM-02 instruction |
| ------------------------------ | ----------------- |
| `MOV A B`                      | `MOV A,B`         |
| `MVI A 0xF8`                   | `MOV A,#$F8`      |
| `MVI B 0xF8`<br />`MVI C 0xA2` | `MOV BC,#$F8A2`   |
| `LD A 0xBF46`                  | `MOV A,$BF46`     |
| `ST A 0xBF46`                  | `MOV $BF46,A`     |
| `LDX A 0xBF46`                 | `MOV A,($BF46)`   |
| `LDR A`                        | `MOV A,(HL)`      |

**The DM-02 supports the following explicit addressing modes:**

| Mode                   | Example notation         | Description                                                  |
| ---------------------- | ------------------------ | ------------------------------------------------------------ |
| Absolute register      | A                        | Refers to a register to get data from or write data to       |
| Absolute register pair | BC                       | Refers to a register pair (BC or HL) to get data from or write data to |
| Immediate value        | #$FF                     | Defines immediate data                                       |
| Absolute address       | $FA6C                    | Defines a memory address to get data from or write data to   |
| Indirect address       | ($FA6C)                  | Defines a memory address, that contains the memory address to get data from or write data to |
| Indirect register      | (HL)                     | Refers to a register pair, that contains the memory address to get data from or write data to |
| *Indexed modes*        | *$B47E+A*<br>*($B47E+A)* | _**Currently not supported**, but may be implemented in the future_ |

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

**Note:** 16-bit values must always be expressed in hexadecimal format, preferably with all 4 characters to avoid confusion by the assembler (e.g., `$003A`).

<a name="strings"></a>

### Strings

Defining strings is pretty straight forward as you can see in the example. Some characters require the use of the `\` **escape character** in order to be expressed.

To use an escape character simply write the **2 character** hexadecimal code, prefixed with a backslash:

```
"This is a carriage return: \0D" _
"This is a horizontal tab: \09"
```

If the string definition spans multiple lines, an underscore is required to indicate the string terminator should not be applied.



<a name="memory-layout"></a>

## Memory layout

| Start address | End address | Description             |
| ------------- | ----------- | ----------------------- |
| 0000          | 3FFF        | ROM                     |
| 4000          | FEFF        | RAM                     |
| FEFF          | 4000        | Stack space (suggested) |
| FF00          | FFFF        | I/O                     |

**Notes:**

- No zero-page addressing support (may be added in future)
- Stack space starts at the end of RAM and works its way back to the start when data is pushed onto it, therefore the entire RAM may technically be used as stack space.

### Program storage

The machine code produced by the assembler follows this structure:

1. Bootloader
2. Pre-defined data
3. Program code

### Bootloader

The assembler adds bootloader code at the start of memory (either address `$0000` or at the offset if it's defined). This code performs a jump to the start of the program code.

This is needed because data that is pre-defined in the program is stored before any of the instructions.

If a program needs to run from RAM, the bootloader code must be present in the ROM because execution always starts at address zero.



<a name="instruction-reference"></a>

## Instruction reference

<a name="MOV"></a>

### MOV

|                                     |
| ----------------------------------- |
| MOV A,B                             |
| MOV A,C                             |
| MOV A,H                             |
| MOV A,L                             |
| MOV B,A                             |
| MOV B,C                             |
| MOV B,H                             |
| MOV B,L                             |
| MOV C,A                             |
| MOV C,B                             |
| MOV C,H                             |
| MOV C,L                             |
| MOV H,A                             |
| MOV H,B                             |
| MOV H,C                             |
| MOV H,L                             |
| MOV L,A                             |
| MOV L,B                             |
| MOV L,C                             |
| MOV L,H                             |
| MOV BC,HL                           |
| MOV HL,BC                           |
| MOV A,#$value                       |
| MOV B,#$value                       |
| MOV C,#$value                       |
| MOV H,#$value                       |
| MOV L,#$value                       |
| MOV BC,#$value                      |
| MOV HL,#$value                      |
| MOV A,$address *(overwrites HL)*    |
| MOV B,$address *(overwrites HL)*    |
| MOV C,$address *(overwrites HL)*    |
| MOV BC,$address *(overwrites HL)*   |
| MOV HL,$address                     |
| MOV $address,A *(overwrites HL)*    |
| MOV $address,B *(overwrites HL)*    |
| MOV $address,C *(overwrites HL)*    |
| MOV $address,BC *(overwrites HL)*   |
| MOV $address,HL *(overwrites BC)*   |
| MOV A,($address) *(overwrites HL)*  |
| MOV B,($address) *(overwrites HL)*  |
| MOV C,($address) *(overwrites HL)*  |
| MOV BC,($address) *(overwrites HL)* |
| MOV ($address),A *(overwrites HL)*  |
| MOV ($address),B *(overwrites HL)*  |
| MOV ($address),C *(overwrites HL)*  |
| MOV ($address),BC *(overwrites HL)* |
| MOV A,(BC)                          |
| MOV H,(BC)                          |
| MOV L,(BC)                          |
| MOV A,(HL)                          |
| MOV B,(HL)                          |
| MOV C,(HL)                          |
| MOV (BC),A                          |
| MOV (BC),H                          |
| MOV (BC),L                          |
| MOV (HL),A                          |
| MOV (HL),B                          |
| MOV (HL),C                          |
| MOV BC,(HL)                         |
| MOV HL,(BC)                         |
| MOV (HL),BC                         |
| MPV (BC),HL                         |

<a name="SP"></a>

### SP

|             |
| ----------- |
| SP $address |

<a name="PUSH"></a>

### PUSH

| *Requires SP to be executed first* |
| ---------------------------------- |
| PUSH A                             |
| PUSH B                             |
| PUSH C                             |
| PUSH H                             |
| PUSH L                             |
| PUSH BC                            |
| PUSH HL                            |
| PUSH F                             |

<a name="POP"></a>

### POP

| *Requires PUSH to be executed first* |
| ------------------------------------ |
| POP A                                |
| POP B                                |
| POP C                                |
| POP H                                |
| POP L                                |
| POP BC                               |
| POP HL                               |
| POP F                                |

<a name="ADD"></a>
### ADD

|                                  |
| -------------------------------- |
| ADD A                            |
| ADD B                            |
| ADD C                            |
| ADD H                            |
| ADD L                            |
| ADD #$value                      |
| ADD $address *(overwrites HL)*   |
| ADD ($address) *(overwrites HL)* |
| ADD (HL)                         |

<a name="ADC"></a>
### ADC

|                                  |
| -------------------------------- |
| ADC A                            |
| ADC B                            |
| ADC C                            |
| ADC H                            |
| ADC L                            |
| ADC #$value                      |
| ADC $address *(overwrites HL)*   |
| ADC ($address) *(overwrites HL)* |
| ADC (HL)                         |

<a name="SUB"></a>
### SUB

|                                  |
| -------------------------------- |
| SUB A                            |
| SUB B                            |
| SUB C                            |
| SUB H                            |
| SUB L                            |
| SUB #$value                      |
| SUB $address *(overwrites HL)*   |
| SUB ($address) *(overwrites HL)* |
| SUB (HL)                         |

<a name="SBC"></a>
### SBC

|                                  |
| -------------------------------- |
| SBC A                            |
| SBC B                            |
| SBC C                            |
| SBC H                            |
| SBC L                            |
| SBC #$value                      |
| SBC $address *(overwrites HL)*   |
| SBC ($address) *(overwrites HL)* |
| SBC (HL)                         |

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

|                                               |
| --------------------------------------------- |
| NOT A                                         |
| NOT B *(affects register it is performed on)* |
| NOT C *(affects register it is performed on)* |
| NOT H *(affects register it is performed on)* |
| NOT L *(affects register it is performed on)* |
| *NOT #$value*                                 |
| *NOT $address*                                |
| *NOT ($address)*                              |
| *NOT (HL)*                                    |

<a name="SHL"></a>

### SHL

|                                               |
| --------------------------------------------- |
| SHL A                                         |
| SHL B |
| SHL C |
| SHL H |
| SHL L |
| *SHL #$value*                                 |

<a name="SHR"></a>
### SHR

|                                               |
| --------------------------------------------- |
| SHR B |
| SHR C |
| SHR H |
| SHR L  |
| *SHR #$value*                                 |

<a name="ASR"></a>
### ASR

|                                               |
| --------------------------------------------- |
| ASR B |
| ASR C |
| ASR H |
| ASR L  |
| *ASR #$value*                                 |

<a name="ROL"></a>
### ROL

|                  |
| ---------------- |
| ROL B            |
| ROL C            |
| ROL H            |
| ROL L            |
| *ROL #$value*    |

<a name="ROR"></a>
### ROR

|                  |
| ---------------- |
| ROR B            |
| ROR C            |
| ROR H            |
| ROR L            |
| *ROR #$value*    |

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

Compare result:

|Carry|Zero|Meaning|
|-|-|-|
| 1 | 0 | A < B |
| 0 | 1 | A == B |
| 0 | 0 | A > B |

<a name="JMP"></a>

### JMP

<a name="JMPc"></a>

### JMP (conditional)

|              |
| ------------ |
| JC $address  |
| JZ $address  |
| JN $address  |
| JO $address  |
| JNC $address |
| JNZ $address |
| JP $address  |
| JNO $address |

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

*Check for use within label*

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