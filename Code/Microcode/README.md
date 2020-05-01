# DM-02 Microcode Compiler

This application is used to compile the microcode definition, as defined in the `microcode.src` file, into a binary image that is loaded into the DM-02 Computer's microcode ROM.

It's a .NET Core application that can compile and run on Windows, macOS and Linux.

## Usage
- Execute: `sh mcc.sh`
- Upload the contents of the `.rom` file into the DM-02's microcode ROM.
- The `.img` file can be used as image for the microcode ROM in the Logisim circuit.