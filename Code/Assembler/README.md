# DM-02 Assembler

This application is used to compile DM-02 Computer assembly files to DM-02 Computer machine code.
It's a .NET Core application that can compile and run on Windows, macOS and Linux.

## Usage
- Build the application: `dotnet build src`
- Run the application: `dotnet ./src/Asm/bin/Debug/netcoreapp2.2/asm.dll ../Microcode/microcode.src programs/example/example.asm`
- Upload the contents of the `.rom` file into the DM-02's memory.
- The `.img` file can be used as image for the Logisim circuit.

## Shell script
- To use the shell script that assembles the example, just execute: `sh asm.sh`.