﻿using System;
using System.IO;

namespace Mcc
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine();
            Console.WriteLine("---------------------------------");
            Console.WriteLine("DM-02 Computer Microcode Compiler");
            Console.WriteLine("---------------------------------");
            Console.WriteLine();

            args = new [] { @"/media/ruud/ntfs/Personal/Projects/Active/DM-02/Code/Microcode/microcode.src" };

            if (args.Length == 0)
            {
                Console.WriteLine("Usage: mcc.exe \"filename.src\"");
                Console.WriteLine("Outputs \"filename.bin\" binary file.");
                Console.WriteLine();
                return;
            }

            string fileName = args[0];
            
            if (!File.Exists(fileName))
            {
                Console.WriteLine($"Could not find source file {fileName}");
                Console.WriteLine();
                return;
            }

            try
            {
                Compiler.Compile(fileName);
            }
            catch (CompilerException ex)
            {
                Console.WriteLine("Compilation failed:");
                Console.WriteLine(ex?.Message);
            }

            Console.WriteLine();
        }
    }
}
