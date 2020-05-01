using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;

namespace Asm
{
    public class Assembler
    {
        private const int BOOTLOADER_SIZE = 16;
        private const byte SP_INSTRUCTION = 0x42;
        private readonly byte[] LABEL_INSTRUCTIONS = { 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0XC8, 0xC9, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF, 0xD0, 0xD1, 0xD2, 0xD2, 0xD3, 0xD4 };
        private readonly byte[] STACK_INSTRUCTIONS = { 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x51, 0x52, 0xCC, 0xCD, 0xCE, 0xCE, 0xCF, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4 };

        private static Assembler _assembler;
        private Mcc.Compiler microcodeCompiler;

        private string source;
        private string sourceFolderPath;
        private byte[] machineCode = new byte[0xBFFF];        
        private int machineCodeAddress = BOOTLOADER_SIZE;   // The first 16 bytes of machine code are reserved
                                                            // for a JMP to get past the predefined data and maybe additional code in the future.
        private int offset = 0;

        private Dictionary<string, int> labels = new Dictionary<string, int>();
        private Dictionary<int, string> labelsToTranslate = new Dictionary<int, string>();
        private Dictionary<string, int> addressVariables = new Dictionary<string, int>();
        private Dictionary<string, string> constants = new Dictionary<string, string>();

        public static void Assemble(string microcodeSourceFilePath, string programSourceFilePath)
        {
            string romFileName = programSourceFilePath.Split('.', StringSplitOptions.RemoveEmptyEntries).First() + ".rom";
            string logisimImageFileName = programSourceFilePath.Split('.', StringSplitOptions.RemoveEmptyEntries).First() + ".img";

            _assembler = new Assembler(microcodeSourceFilePath, programSourceFilePath);
            _assembler.Assemble();
            _assembler.Save(romFileName, logisimImageFileName);
        }

        private Assembler(string microcodeSourceFilePath, string programSourceFilePath)
        {
            LoadMicrocode(microcodeSourceFilePath);

            string programCode = File.ReadAllText(programSourceFilePath);

            this.sourceFolderPath = Path.GetDirectoryName(programSourceFilePath);
            this.source = StringUtils.Cleanup(programCode);
        }

        private void Assemble()
        {
            var sw = Stopwatch.StartNew();
            Console.WriteLine("Generating machine code...");

            try
            {
                ProcessIncludes();          // Include external files.
                ProcessOffset();            // Determine the memory offset.
                ProcessDataBlocks();        // Add predefined data to the machine code.
                ProcessConstants();         // Replace constants in code with their value.
                ProcessAddressVariables();  // Replace any address variables with their address.
                ProcessAssembly();          // Convert the assembly to machine code.
            }
            catch (IndexOutOfRangeException ex)
            {
                throw new AssemblerException("Generated machine code size exceeds maximum of 48 Kb");
            }

            if (machineCodeAddress >= 0x4000)
            {
                Console.WriteLine("\nWARNING: Generated machine code size exceeds 16 Kb and will not fit into ROM!");
            }

            Console.WriteLine();
            Console.WriteLine($"{machineCodeAddress} bytes of machinecode generated in {sw.ElapsedMilliseconds} ms.");
        }

        public void Save(string romFileName, string logisimImageFileName)
        {
            var sw = Stopwatch.StartNew();
            Console.Write("Writing machine code to output files...");

            if (File.Exists(romFileName))
            {
                File.Delete(romFileName);
            }

            if (File.Exists(logisimImageFileName))
            {
                File.Delete(logisimImageFileName);
            }

            using (var writer = new BinaryWriter(File.Open(romFileName, FileMode.CreateNew)))
            {
                writer.Seek(0, SeekOrigin.Begin);
                writer.Write(machineCode);
            }

            using (TextWriter writer = new StreamWriter(File.Open(logisimImageFileName, FileMode.CreateNew)))
            {
                // The Logisim image is written in a plain text format.
                // It has 8 bytes per row, separated by space.
                writer.WriteLine("v2.0 raw\n");
                int address = 0;

                for (int row = 0; row < (machineCodeAddress + BOOTLOADER_SIZE) / 8; row++)
                {
                    string rowData = string.Empty;

                    for (int col = 0; col < 8; col++)
                    {
                        rowData += $"{machineCode[address++]:X2} ";
                    }

                    writer.WriteLine(rowData.Trim());
                }
            }

            Console.WriteLine($"Done in {sw.ElapsedMilliseconds} ms.");
        }

        private void ProcessIncludes()
        {
            while (source.IndexOf(".include") > -1)
            {
                int start = source.IndexOf(".include");
                string includeFilePath = Path.Combine(sourceFolderPath, StringUtils.ExtractStringData(source, start));

                string before = source.Substring(0, start);
                string after = source.Substring(source.IndexOf("\n", start));

                try
                {
                    source = before + File.ReadAllText(includeFilePath) + after;
                }
                catch (Exception ex)
                {
                    throw new AssemblerException($"Could not include file {includeFilePath}\nException: {ex.Message}");
                }
            }

            source = StringUtils.Cleanup(source);
        }

        private void ProcessOffset()
        {
            while (source.IndexOf(".offset") > -1)
            {
                int start = source.IndexOf(".offset");
                string line = StringUtils.GetUntilEndOfLine(source, start);

                offset = StringUtils.ParseUshortValue(line.Split(' ', StringSplitOptions.RemoveEmptyEntries).Last());
                Console.WriteLine($"Offset set at address {offset:X4}");
                
                string before = source.Substring(0, start);
                string after = source.Substring(source.IndexOf("\n", start));
                source = before + after;
            }

            machineCodeAddress = offset + BOOTLOADER_SIZE;
        }

        private void ProcessDataBlocks()
        {
            if (source.IndexOf(".code\n") == -1)
            {
                throw new AssemblerException("Required block '.code' was not found.");
            }

            if (source.IndexOf(".data\n") == -1)
            {
                source = source.Replace(".code\n", string.Empty);
                Console.WriteLine("Optional block '.data' was found.");
                return;
            }

            int start = source.IndexOf(".data\n");

            int endAtNextData = source.IndexOf(".data\n", start + 1);
            int endAtCode = source.IndexOf(".code\n", start);
            int end = source.Length;

            if (endAtNextData > -1 && (endAtNextData < endAtCode || endAtCode == -1))
            {
                end = endAtNextData;
            }
            else if (endAtCode > -1)
            {
                end = endAtCode;
            }

            // Process the current block of data.
            string block = source.Substring(start, end - start);
            ProcessDataBlock(block);

            // Remove from the processed block from the source.
            string before = source.Substring(0, start);
            string after = source.Substring(end);
            source = before + after;

            if (source.IndexOf(".data\n") > -1)
            {
                ProcessDataBlocks();
            }
            else
            {
                source = source.Replace(".code\n", string.Empty);
                Console.WriteLine($"Processed {machineCodeAddress-BOOTLOADER_SIZE} bytes of predefined data.\n");
            }
        }

        private void ProcessDataBlock(string block)
        {
            block = block.Substring(5).Trim('\n');
            var lines = block.Split('\n', StringSplitOptions.RemoveEmptyEntries);

            for (int l = 0; l < lines.Length; l++)
            {
                var nameAndData = lines[l].Split(':', StringSplitOptions.RemoveEmptyEntries).Select(x => x.Trim()).ToArray();
                string dataString = nameAndData.Last();
                
                if (nameAndData.Length == 2 && !nameAndData[0].StartsWith('"'))
                {
                    if (addressVariables.ContainsKey(nameAndData[0]))
                    {
                        throw new AssemblerException($"Address variable '{nameAndData[0]}' was defined more than once.");
                    }

                    if (nameAndData[0].StartsWith("~"))
                    {
                        constants.Add(nameAndData[0], dataString);
                        continue;
                    }

                    if (dataString.StartsWith("$") && dataString.Length == 5)
                    {
                        // Explicit pointer definition.
                        addressVariables.Add(nameAndData[0], StringUtils.ParseUshortValue(dataString));
                        continue;
                    }
                    else
                    {
                        addressVariables.Add(nameAndData[0], machineCodeAddress);
                    }

                    if (dataString.StartsWith("["))
                    {
                        // Defined a length for the current variable.
                        string lengthString = dataString.Replace("[", string.Empty).Replace("]", string.Empty);
                        int length = dataString.StartsWith("$")
                            ? StringUtils.ParseUshortValue(lengthString)
                            : int.Parse(lengthString);

                        machineCodeAddress += length;
                        continue;
                    }
                }
                else if (nameAndData.Length > 2 || (nameAndData.Length == 2 && nameAndData[0].StartsWith('"')))
                {
                    throw new AssemblerException($"Do not use colons in string definitions.\nCheck this line: {lines[l]}");
                }

                byte[] data = StringUtils.ParseDataValue(dataString);
                foreach (byte b in data)
                {
                    machineCode[machineCodeAddress++] = b;
                }
            }
        }

        private void ProcessConstants()
        {
            // Start replacing constants in the source, in order of constant name length (longest first).
            constants.OrderByDescending(kvp => kvp.Key.Length)
                .ToList()
                .ForEach(kvp => source = source.Replace(kvp.Key, kvp.Value));
        }

        private void ProcessAddressVariables()
        {
            // Start replacing variables in the source, in order of variable name length (longest first).
            var ordered = addressVariables.OrderByDescending(kvp => kvp.Key.Length);

            foreach (var kvp in ordered)
            {
                string variable = kvp.Key;
                int address = kvp.Value;

                source = source.Replace(variable, $"${address:X4}");
            }
        }

        private void ProcessAssembly()
        {
            string[] consoleLog = new string[0xBFFF];
            bool stackPointerUsed = false;
            bool stackPointerSet = false;

            var lines = source.Split('\n', StringSplitOptions.RemoveEmptyEntries);

            if (!lines.Contains("main:"))
            {
                throw new AssemblerException("Required label 'main' could not be found.");
            }

            for (int l = 0; l < lines.Length; l++)
            {
                string line = lines[l];

                if (l == 0 && !line.Contains(":"))
                {
                    Console.WriteLine("WARNING: Program code does not start with a label. Consider adding one!");
                }
                
                if (ProcessLabelDefinition(line, machineCodeAddress))
                {
                    // Current line defines a label.
                    continue;
                }
                
                // Find instruction definition for current line.
                string data = null;
                Mcc.Models.Instruction instruction = FindInstruction(line, out data);
                
                if (instruction == null)
                {
                    throw new AssemblerException($"Instruction not defined: {line}");
                }

                if (STACK_INSTRUCTIONS.Contains(instruction.Opcode))
                {
                    stackPointerUsed = true;
                }

                if (instruction.Opcode == SP_INSTRUCTION)
                {
                    stackPointerSet = true;
                }

                // Add the current instruction to the machinecode.
                consoleLog[machineCodeAddress] = line;
                machineCode[machineCodeAddress++] = instruction.Opcode;
                
                if (LABEL_INSTRUCTIONS.Contains(instruction.Opcode))
                {
                    // Current instruction refers to a label.
                    // We need to fill in the label address later.
                    labelsToTranslate.Add(machineCodeAddress, line.Split(' ').Last());
                    machineCodeAddress += 2;
                }
                else if (instruction.ByteCount > 1)
                {
                    if (instruction.ByteCount == 2)
                    {
                        // There is one operand which is a hex value representing one byte.
                        machineCode[machineCodeAddress++] = StringUtils.ParseByteValue(data);
                    }
                    else if (instruction.ByteCount == 3)
                    {
                        // There is one operand which is a hex value representing two bytes. 
                        var bytes = BitConverter.GetBytes(StringUtils.ParseUshortValue(data));
                        machineCode[machineCodeAddress++] = bytes[1];
                        machineCode[machineCodeAddress++] = bytes[0];
                    }
                }
            }

            // If an instruction was used to relies on the Stack Pointer, make sure the stack pointer was set.
            if (stackPointerUsed && !stackPointerSet)
            {
                throw new AssemblerException("Stack Pointer was not set. Execute 'SP' before attempting to use stack.");
            }

            // Fill in the addresses of all label references.
            foreach (var labelref in labelsToTranslate)
            {
                int refAddress = labelref.Key;
                int labelAddress = labels[labelref.Value];

                // Split label address into two bytes.
                var bytes = BitConverter.GetBytes(labelAddress);
                machineCode[refAddress] = bytes[1];
                machineCode[refAddress + 1] = bytes[0];
            }

            // Add bootloader code at the start of the machine code to jump to the program code.
            AddBootLoader();
            consoleLog[offset] = "JMP main";
            
            // Output the address pointer variables to the console.
            Console.WriteLine();

            if (addressVariables.Count > 0)
            {
                int maxNameLength = addressVariables.Keys.OrderByDescending(k => k.Length).First().Length;

                addressVariables.OrderBy(kvp => kvp.Value)
                    .ToList()
                    .ForEach(kvp => Console.WriteLine($"{kvp.Key}{"".PadLeft(maxNameLength - kvp.Key.Length)} : ${kvp.Value:X4}"));

                Console.WriteLine();
            }

            // Output the machinecode with assembly to the console.
            for (int i = offset; i < machineCodeAddress; i++)
            {
                string loginstruction = consoleLog[i];

                if (labels.ContainsValue(i))
                {
                    Console.WriteLine($"{labels.FirstOrDefault(x => x.Value == i).Key}:");
                }

                if (addressVariables.ContainsValue(i))
                {
                    loginstruction = addressVariables.FirstOrDefault(x => x.Value == i).Key;
                }

                if (!string.IsNullOrEmpty(loginstruction))
                {
                    loginstruction = "\t; " + loginstruction;
                }

                Console.WriteLine($"${i:X4}: ${machineCode[i]:X2}{loginstruction}");
            }
        }

        /// <summary>
        /// Finds the instruction that is used in the given line of assembly code.
        /// </summary>
        /// <param name="line"></param>
        /// <param name="data">If the line of code contains data (value or address), it's output here.</param>
        /// <returns></returns>
        public Mcc.Models.Instruction FindInstruction(string line, out string data)
        {
            // First check if there is an exact match.
            var instruction = microcodeCompiler.Instructions.FirstOrDefault(x => x.Mnemonic.Equals(line));

            if (instruction != null)
            {
                data = null;
                return instruction;
            }

            if (line.Contains("#"))
            {
                string mnemonic = line.Contains(",")
                        ? line.Split(',').First() + ",value"
                        : line.Split('#').First() + "value";
                
                data = line.Split('#').Last();

                instruction = microcodeCompiler.Instructions.FirstOrDefault(x => x.Mnemonic.Equals(mnemonic));

                if (instruction != null)
                {
                    return instruction;
                }
            }

            foreach (var i in microcodeCompiler.Instructions.Where(x => x.Mnemonic.Contains("address")))
            {
                string[] beforeAfter = i.Mnemonic.Split("address");

                if (line.StartsWith(beforeAfter[0]) && (string.IsNullOrEmpty(beforeAfter[1]) || line.EndsWith(beforeAfter[1])))
                {
                    data = line.Replace(beforeAfter[0], "");
                    if (!string.IsNullOrEmpty(beforeAfter[1]))
                    {
                        data = data.Replace(beforeAfter[1], "");
                    }

                    if (i.Mnemonic.Replace("address", data).Equals(line))
                    {
                        return i;
                    }
                }
            }

            data = null;
            return null;
        }

        private void AddBootLoader()
        {
            // Jump to main label
            int mainAddress = labels["main"];
            var bytes = BitConverter.GetBytes(mainAddress);

            machineCode[offset] = 0xC3;         // JMP
            machineCode[offset+1] = bytes[1];   // high byte
            machineCode[offset+2] = bytes[0];   // low byte
        }
        
        private bool ProcessLabelDefinition(string line, int address)
        {
            if (line.EndsWith(":"))
            {
                string label = line.Split(':').First();

                if (labels.ContainsKey(label))
                {
                    throw new AssemblerException($"Label '{label}' is defined more than once.");
                }

                labels.Add(label, address);

                return true;
            }

            return false;
        }
        
        private void LoadMicrocode(string microcodeSourceFile)
        {
            Console.WriteLine("Loading microcode definition...");

            this.microcodeCompiler = Mcc.Compiler.Compile(microcodeSourceFile, false);

            Console.WriteLine("Microcode loaded!");
            Console.WriteLine();
        }
    }
}
