# Microcode

*This documentation is still in progress...*



DM-01 used 19 address lines for the microcode ROM and stored state of 48 control lines in 6 separate bytes. The linear approach is not very scalable and also made the control unit very complex, because it had to retrieve 6 bytes of data for each microinstruction; this approach is the main reason the project failed.

The big lesson I took from this is that the control line states need to be stored in encoded form in order to limit the amount of data stored and simplify the process of getting the data out of the ROM and into the control unit.

This is how microcode is managed in the DM-02:

- I use a microcode ROM with 16 address lines and 16-bit words (M27C1024).
- Each microinstruction is stored in one 16-bit word. This means we no longer need to store 6 separate words for each instruction and therefore we don't need the additional 3 address lines.
- The first 2 t-states (fetch cycle) are hard-wired into the controller and excluded from the microcode ROM. We have 4 bits reserved in the ROM address for the t-state, so we can have 16 t-states defined in microcode. This means a total of 18 t-states per instruction, including the 2 t-states required for the fetch cycle.
- The microinstruction (which basically represents control line states) is encoded so it fits in 16 bits. The controller (control unit) does decoding to translate the 16-bit word back to all control line states.
- I/O is controlled using memory addressing instead of register operations (less control lines required)
- The microinstruction ROM address is constructed as such:  
  `xxxxxxxx|xxxx|xxxx` (16-bits)  
  `instruction|t-state|flags`

The address is `(opcode << 8) | (tstate << 4) | flags`, with `N Z O C` from
high to low in the four-bit flag field. The compiler writes all 65,536 words:
131,072 little-endian bytes in `.rom`, and 65,536 hexadecimal words after the
`v2.0 raw` header in `.img`. Unassigned words are zero-filled. This storage
policy does not define a safe invalid-opcode response.

The separate [CW1 controller candidate](./Control-word.md) implements this
logical 64K×16 image with two AT27C512R-70PU 64K×8 byte banks. It captures the
control word on C1 PH1, enables decoded controls during PH2 and drives PC1's
PH3 capture. The historical CLOCK1/CLOCK2 descriptions below are architectural
phase roles; CW1's explicit blanking and timing contract is documented separately.
Fetch and t-state sequencing are external to CW1 and implemented in the separate
[SQ1 candidate](./Sequencer.md), including retained HALT/request arbitration.



## Microcode control words

The microcode rom can output two types of 16-bit control words:

- Data operation word
- Function operation word

each type of word has its own bit format:

### Data operation word format

`1|xxxx|xxxx|x|xxxxx|0`  
`1|operand_out|operand_load|0|0|function|0`<br>
`1|operand_out|operand_load|1|alu_operation|0`

> The *out* operation starts at rising CLOCK1
> The *load* operation starts at rising CLOCK2
> The *function* operation may start at rising CLOCK1 or CLOCK2, depending on the function
> The *alu_operation* does not depend on a clock signal

### Function operation word format

`0|xxxx|000000|xxxx|0`  
`0|function|000000|function|0`

> Controls up to 2 lines at once (we have room for one more in the control word, but takes an additional line decoder to use it).
> Not all control lines may be combined in one operation word.

### Data operation operands

With the *operand_out* and *operand_load* in the microinstruction word, we control what part of the computer will output data to the bus and what will load that data.

The following operands can be used in this operation:

| Operand    | Description                              | Bits   |
| ---------- | ---------------------------------------- | ------ |
| A          | Accumulator                              | `0001` |
| B          | B register                               | `0010` |
| C          | C register                               | `0011` |
| H          | H register                               | `0100` |
| L          | L register                               | `0101` |
| ALU        | Capture ALU result / output captured result | `0110` |
| F          | Flags register                           | `0111` |
| MAR_H      | Memory Access Register address high byte | `1000` |
| MAR_L      | Memory Access Register address low byte  | `1001` |
| MEM        | Memory                                   | `1010` |
| PC_H       | Program Counter high byte                | `1011` |
| PC_L       | Program Counter low byte                 | `1100` |
| STK_H      | Stack Pointer high byte                  | `1101` |
| STK_L      | Stack Pointer low byte                   | `1110` |
| *not used* | *available for future use*               | `1111` |

### Functions	

With the *function* in the microinstruction word, we control what control lines (that are not used for output to or loading from the bus) are enabled.

The following functions can be used in this operation:

| Control line     | Function                                                     | Bits   |
| ---------------- | ------------------------------------------------------------ | ------ |
| TSTATE_reset     | Reset t-state sequence (start new fetch cycle)               | `0001` |
| CLOCK_halt       | Halt the clock until it's manually continued                 | `0010` |
| STK_inc          | Increase the Stack Pointer by one                            | `0011` |
| STK_dec          | Decrease the Stack Pointer by one                            | `0100` |
| PC_inc           | Increase the Program Counter by one                          | `0101` |
| PC_MAR_transfer  | Transfer the Program Counter value to the Memory Access Register | `0110` |
| STK_MAR_transfer | Transfer the Stack Pointer value to the Memory Access Register | `0111` |
| MAR_inc          | Increase the Memory Access Register by one                   | `1000` |
| FSET_z           | Set the Zero flag                                            | `1001` |
| FSET_c           | Set the Carry flag                                           | `1010` |
| FCLR_z           | Clear the Zero flag                                          | `1011` |
| FCLR_c           | Clear the Carry flag                                         | `1100` |
| *not used*       | *available for future use*                                   | `1101` |
| *not used*       | *available for future use*                                   | `1110` |
| *not used*       | *available for future use*                                   | `1111` |

### ALU operations

Refer to the [ALU and Flags](./ALU-and-flags.md) documentation for the available ALU operations.

### Example

Let's take the microcode that was used as an example in the [Clock signals and timing](./Clock-signals-timing.md) documentation:

```
FETCH:      PC_MAR_transfer  # The fetch cycle is hard-wired in the controller circuit
            IR_load
            MEM_out
            PC_inc

TSTATE_0:   PC_MAR_transfer  # Data microinstruction
            MEM_out	
            A_load
			
TSTATE_1:   PC_inc           # Misc. microinstruction
            TSTATE_reset
```

When compiled, this will result in 2 microinstruction words (the fetch cycle is hard-wired, so only the code for t-state 0 and 1 are compiled into the ROM).

The first word is `1|1010|0001|0|0|0110|0`, or `0xD08C`:

- Bit 15 selects a data operation.
- Output `1010` selects MEM; load `0001` selects A.
- Bit 6 is zero, selecting a function rather than an ALU operation; bit 5 is unused.
- Function `0110` selects PC_MAR_transfer; bit 0 is unused.

The second word is `0|0101|000000|0001|0`, or `0x2802`:

- Bit 15 selects a function operation.
- Function `0101` selects PC_inc; function `0001` selects TSTATE_reset.
- Bits 10–5 and bit 0 are unused.

For `MOV A,value` (opcode `0x17`), these words occupy addresses `0x1700`–`0x170F`
and `0x1710`–`0x171F`, respectively, covering all 16 flag states.

## Execution verification

`Verification/dm02/microcode.py` independently expands source definitions and
checks every generated word. `Verification/dm02/control.py` executes the compiled
words with the generated ALU ROM and compares architectural effects under six
explicit phase/flag-capture profiles, including extracted Logisim PC logic.
JMP and CALL no longer assert PC_inc alongside PC_L_load: the old low byte could
otherwise produce a carry into the target high byte. The boundary audit checks
204,800 target/flag/operand-PC cases and reproduces the old defect by mutation.
See [the verification runbook](../Verification/README.md) for scope, the scratch
register contract and remaining physical controller/flag-wiring work.
