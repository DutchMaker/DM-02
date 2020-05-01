# Using the Logisim circuit

Just a very short instruction for using the Logisim circuit.

## First time use

1. Latest microcode is already preloaded in the microcode rom.
2. Load the example program image (`example.img`) into the ROM:
   1. Open the Memory circuit.
   2. Right-click the ROM (the top one) and choose *Load Image*...
   3. Select the `example.img` file.
3. Make sure the circuit is reset (Ctrl+R on Windows or ⌘+R on macOS).
4. Set the Tick Frequency to 4.1 Khz
5. Enable the Ticks (Ctrl+K on Windows or ⌘+K on macOS).
6. The program will now execute

## Replacing the microcode

1. Use the microcode compiler to generate new image files based on the `microcode.src` source file.
2. Load the microcode image file into the microcode ROM using the *Load Image* function.

## Running other programs

Simply run the assembler on your own `.asm` files to generate an `.img` file for the program.  
Then load it into the ROM or RAM, like explained with the example.

When running from RAM, please note that a circuit reset will also clear the RAM!
You can perform a soft reset by clicking on the `RESET` button in the top left corner of the main circuit. If you leave `RESET_RAM` set to zero, it will not clear the RAM.

## Debugging

Debugging programs (or the circuit itself) can be quite challenging, but there are a few things in place that may help:

- You can set hardware breakpoints by attaching the `brkpnt0` (up to `brkpnt4`) label to any control line. The computer will then halt when the line goes high.
- You can set software breakpoints by executing the `HALT` instruction.
- You can also manually halt by clicking the `BREAK` button in the top left corner.
- After a halt you can resume execution by clicking the `CONTINUE` button in the top left corner.