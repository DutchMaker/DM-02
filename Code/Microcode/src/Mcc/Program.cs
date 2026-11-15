using System;
using System.IO;

namespace Mcc
{
    class Program
    {
        static int Main(string[] args)
        {
            Console.WriteLine();
            Console.WriteLine("---------------------------------");
            Console.WriteLine("DM-02 Computer Microcode Compiler");
            Console.WriteLine("---------------------------------");
            Console.WriteLine();

            //args = new [] { @"/Users/ruud/Projects/DM-02/Code/Microcode/microcode.src" };
            //args = new [] { @"D:\Projects\Active\DM-02\Code\Microcode\microcode.src" };

            if (args.Length != 1)
            {
                Console.WriteLine("Usage: mcc.exe \"filename.src\"");
                Console.WriteLine("Outputs \"filename.img\" (for Logisim) and \"filename.rom\" files.");
                Console.WriteLine();
                return 2;
            }

            string fileName = args[0];
            
            if (!File.Exists(fileName))
            {
                Console.WriteLine($"Could not find source file {fileName}");
                Console.WriteLine();
                return 2;
            }

            try
            {
                Compiler.Compile(fileName);
            }
            catch (CompilerException ex)
            {
                Console.WriteLine("Compilation failed:");
                Console.WriteLine(ex?.Message);
                return 1;
            }

            Console.WriteLine();
            return 0;
        }
    }
}
