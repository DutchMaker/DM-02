# Project status

This document is here to keep track of the project status. 



## Project log

### 2019-10-01:

The Logisim design has all the modules done, except for the Controller. I'll probably build the Microcode Compiler first before starting design of the Controller.

### 2019-09-26:

Started the project log. At this point in the project, countless hours have been put into research and thinking about problems and solutions (related to this computer...). The result of it all has been documented. *Nothing has actually been built yet at this point*.

There will be a bit more documentation work before I start building things. I'm considering using Proteus for simulation instead of Logisim (which I used for DM-01), because it will be easier to simulate the phased clock and it takes propagation delays of IC's into account. 



## Project tasks

The following high-level tasks are waiting to be done (in no particular order):

- Write more documentation as the project progresses.
- Create and maintain the project on Hackaday.
- Simulator circuit design (in Logisim or Proteus, not decided yet).
- Assembly language specification.
- Assembler tooling.
- Microcode language specification.
- Microcode compiler tooling.
- Circuit design.
- PCB design.



## Project ideas & Reminders

Just some things I need to keep track of:

- Support for interrupts
- Store accumulator and flags register on stack before a CALL instruction (or interrupt) and restore it after RET instruction
- VGA graphics (320x200) with dedicated 64kb VRAM
  - Implement using bank switch (direct access to VRAM from program)?
  - or maybe with I/O commands to a separate gfx module
- All counters need reset lines
- TODO

  - Check if I have Zener in stock - also check footprint for Kicad
  - Test power circuit on breadboard
    - Test reset circuit
  - Measure if power + debug board can connect with Arduino in between
  - Create footprint for powerswitch (double pole single throw) - also used in debug board
  - Check if I have angled tact switch in stock - also check footprint
  - Test continue/halt circuit

