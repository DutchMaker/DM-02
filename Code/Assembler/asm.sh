if [ ! -f "src/Asm/bin/Debug/netcoreapp2.2/asm.dll" ]; then
    dotnet build src
fi

dotnet src/Asm/bin/Debug/netcoreapp2.2/asm.dll ../Microcode/microcode.src programs/example/example.asm