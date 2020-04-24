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



## Microcode control words

The microcode rom can output two types of 16-bit control words:

- Data operation word
- Function operation word

each type of word has its own bit format:

### Data operation word format

`1|xxxx|xxxx|x|xxxxx|0`
`1|operand_out|operand_load|0|0|function|0`
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
| ALU        | ALU result *(load only)*                 | `0110` |
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
| CMP              | Compare function (only store ALU flags, not the result)      | `1101` |
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

The first microinstruction is a data operation, so according to the format (`0|operand_out|operand_load|0|function` or `0|operand_out|operand_load|1|alu_operation`), the compiled instruction word  will be:

- `0100100000001110` 
  - `0` to indicate the microinstruction is a data operation.
  - `1001` refers to `MEM` which will be output to the bus.
  - `0000` refers to `A` which will load from the bus.
  - `0` to indicate we are also enabling a function control line.
  - `00111` refers to the `PC_MAR_transfer` control line.
  - `0` because the last bit in the data operation word is not used.

The second microinstruction is a function operation, so according to the format (`1|function|function|function`), the compiled instruction word will be:

- `1001010000100000`
  - `1` to indicate the microinstruction is a function operation.
  - `00101` refers to the `PC_inc` control line.
  - `00001` refers to the `TSTATE_reset` control line.
  - `00000` refers to no control line.

