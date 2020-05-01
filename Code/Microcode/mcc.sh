if [ ! -f "src/Mcc/bin/Debug/netcoreapp2.2/mcc.dll" ]; then
    dotnet build src
fi

dotnet src/Mcc/bin/Debug/netcoreapp2.2/mcc.dll microcode.src