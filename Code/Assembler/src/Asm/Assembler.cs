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

        private readonly string[] LABEL_INSTRUCTIONS = 
        { 
            "JMP", "JC", "JZ", "JN", "JO", "JNC", "JNZ", "JP", "JNO",
            "CALL", "CC", "CZ", "CN", "CO", "CNC", "CNZ", "CP", "CNO"
        };

        private static Assembler _assembler;
        private Mcc.Compiler microcodeCompiler;

        private string source;
        private byte[] machineCode = new byte[0x4000];        
        private ushort machineCodeAddress = BOOTLOADER_SIZE;    // The first 16 bytes of machine code are reserved
                                                                // for a JMP to get past the predefined data and maybe additional code in the future.
        private ushort offset = 0;

        private Dictionary<string, int> labels = new Dictionary<string, int>();
        private Dictionary<int, string> labelsToTranslate = new Dictionary<int, string>();
        private Dictionary<string, int> addressVariables = new Dictionary<string, int>();

        bool dataDefined = false;

        public static void Assemble(string microcodeSourceFile, string programSourceFile)
        {
            string romFileName = programSourceFile.Split('.', StringSplitOptions.RemoveEmptyEntries).First() + ".rom";
            string logisimImageFileName = programSourceFile.Split('.', StringSplitOptions.RemoveEmptyEntries).First() + ".img";
            string programCode = File.ReadAllText(programSourceFile);

            _assembler = new Assembler(microcodeSourceFile, programCode);
            _assembler.Assemble();
            _assembler.Save(romFileName, logisimImageFileName);
        }

        private Assembler(string microcodeSourceFile, string programCode)
        {
            LoadMicrocode(microcodeSourceFile);

            this.source = StringUtils.Cleanup(programCode);
        }

        private void Assemble()
        {
            var sw = Stopwatch.StartNew();
            Console.WriteLine("Generating machinecode...");

            ProcessIncludes();          // Include external files.
            ProcessOffset();            // Determine the memory offset.
            ProcessDataBlocks();        // Add predefined data to the machine code.
            ProcessAddressVariables();  // Replace any address variables with their address.
            ProcessAssembly();
            //Save();                     // Save the machine code to disk.

            Console.WriteLine();
            Console.WriteLine($"{machineCodeAddress} bytes of machinecode generated in {sw.ElapsedMilliseconds} ms.");
        }

        public void Save(string romFileName, string logisimImageFileName)
        {
            var sw = Stopwatch.StartNew();
            Console.Write("Writing data...");

            if (File.Exists(romFileName))
            {
                File.Delete(romFileName);
            }

            if (File.Exists(logisimImageFileName))
            {
                File.Delete(logisimImageFileName);
            }

        // private void SaveMachineCode()
        // {
        //     if (File.Exists(targetFileName))
        //     {
        //         File.Delete(targetFileName);
        //     }

        //     using (var writer = new BinaryWriter(File.Open(targetFileName, FileMode.CreateNew)))
        //     {
        //         writer.Seek(0, SeekOrigin.Begin);
        //         writer.Write(machineCode);
        //     }
        // }

            using (var writer = new BinaryWriter(File.Open(romFileName, FileMode.CreateNew)))
            {
                // // ROM image for EPROM needs to be little-endian format.
                // // (low byte first, high byte second)
                // foreach (int address in this.microcode.Keys)
                // {
                //     byte high = (byte)(this.microcode[address] >> 8);
                //     byte low = (byte)(this.microcode[address] & 0xff);

                //     // The offset is calculated in bytes, our values are 2 bytes each.
                //     // Therefore we need to store at address*2.
                //     writer.Seek(address*2, SeekOrigin.Begin);
                //     writer.Write(low);
                //     writer.Write(high);
                // }
            }

            using (TextWriter writer = new StreamWriter(File.Open(logisimImageFileName, FileMode.CreateNew)))
            {
                // // The Logisim image is written in a plain text format.
                // // It has 8 16-bit values per row, separated by space.
                // // Values are formatted big-endian.
                // writer.WriteLine("v2.0 raw\n");
                // int address = 0;

                // for (int row = 0; row < UInt16.MaxValue / 8; row++)
                // {
                //     string rowData = string.Empty;

                //     for (int col = 0; col < 8; col++)
                //     {
                //         if (this.microcode.ContainsKey(address))
                //         {
                //             rowData += $"{Converter.UIntToHex(this.microcode[address])} ";
                //         }
                //         else
                //         {
                //             rowData += "0000 ";
                //         }

                //         address++;
                //     }

                //     writer.WriteLine(rowData.Trim());
                // }
            }

            Console.WriteLine($"Saved and done ({sw.ElapsedMilliseconds} ms)");
        }

        private void ProcessIncludes()
        {
            while (source.IndexOf(".include") > -1)
            {
                int start = source.IndexOf(".include");
                string includeFileName = StringUtils.ExtractStringData(source, start);

                string before = source.Substring(0, start);
                string after = source.Substring(source.IndexOf("\n", start));

                try
                {
                    source = before + File.ReadAllText(includeFileName) + after;
                }
                catch (Exception ex)
                {
                    throw new AssemblerException($"Could not include file {includeFileName}\nException: {ex.Message}");
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

            dataDefined = true;

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
                Console.WriteLine($"Processed {machineCodeAddress-BOOTLOADER_SIZE} bytes of predefined data.");
            }
        }

        private void ProcessDataBlock(string block)
        {
            dataDefined = true;

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

        private void ProcessAddressVariables()
        {
            // Start replacing variables in the source, in order of variable name length (longest first).
            var ordered = addressVariables.OrderByDescending(kvp => kvp.Key.Length);

            foreach (var kvp in ordered)
            {
                string variable = kvp.Key;
                int address = kvp.Value;

                if (!variable.StartsWith("*"))
                {
                    address += offset;
                }

                source = source.Replace(variable, $"${address:X4}");
            }
        }

        private void ProcessAssembly()
        {
            string[] consoleLog = new string[0x4000];
            var lines = source.Split('\n', StringSplitOptions.RemoveEmptyEntries);

            for (int l = 0; l < lines.Length; l++)
            {
                string line = lines[l];

                if (l == 0 && !line.Equals("main:", StringComparison.OrdinalIgnoreCase))
                {
                    // Ensure that the main label is defined because the bootloader needs this.
                    ProcessLabelDefinition("main:", machineCodeAddress);
                }
                
                if (ProcessLabelDefinition(line, machineCodeAddress))
                {
                    // Current line defines a label.
                    continue;
                }
                machineCodeAddress++;
                // // Find instruction definition for current line.
                // Instruction instruction;
                
                // try
                // {
                //     // TODO:
                //     // FIGURE OUT WHAT INSTRUCTION IS USED
                //     //
                //     //microcodeCompiler.Instructions
                //     // instruction = microcodeCompiler.Instructions.OrderByDescending(x => x.Key.Length)
                //     //     .First(x => line.StartsWith(x.Key));
                // }
                // catch (InvalidOperationException)
                // {
                //     throw new AssemblerException($"Instruction not defined: {line}");
                // }

                // // Add the current instruction to the machinecode.
                // consoleLog[machineCodeAddress] = line;
                // machineCode[machineCodeAddress++] = instruction.Opcode;
                
                // if (LABEL_INSTRUCTIONS.Contains(instruction.Key))
                // {
                //     // Current instruction refers to a label.
                //     // We need to fill in the label address later.
                //     labelsToTranslate.Add(machineCodeAddress, line.Split(' ').Last());
                //     machineCodeAddress += 2;
                // }
                // else if (instruction.ByteCount > 1)
                // {
                //     // Instruction has 1 or 2 operands that need to be stored as well.
                //     var parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);

                //     if (instruction.ByteCount == 2)
                //     {
                //         // There is one operand which is a hex value representing one byte.
                //         //
                //         // TODO:
                //         // GET OPERAND VALUE
                //         machineCode[machineCodeAddress++] = 0; //Convert.ToByte(parts[parts.Length - 1], 16);
                //     }
                //     else if (instruction.ByteCount == 3)
                //     {
                //         // There is one operand which is a hex value representing two bytes. 
                //         //
                //         // TODO:
                //         // GET OPERAND VALUE
                //         //var bytes = BitConverter.GetBytes(Convert.ToInt32(parts[parts.Length - 1], 16));
                //         //machineCode[address++] = bytes[1];
                //         //machineCode[address++] = bytes[0];
                //         machineCode[machineCodeAddress++] = 0;
                //         machineCode[machineCodeAddress++] = 0;
                //     }
                // }
            }

            // Fill in the addresses of all label references.
            foreach (var labelref in labelsToTranslate)
            {
                int refAddress = labelref.Key;
                int labelAddress = labels[labelref.Value] + offset;

                // Split label address into two bytes.
                var bytes = BitConverter.GetBytes(labelAddress);
                machineCode[refAddress] = bytes[1];
                machineCode[refAddress + 1] = bytes[0];
            }

            // Add bootloader code at the start of the machine code to jump to the program code.
            AddBootLoader();

            // Output the machinecode with assembly to the console.
            for (int i = 0; i < machineCodeAddress; i++)
            {
                if (labels.ContainsValue(i))
                {
                    Console.WriteLine($":{labels.FirstOrDefault(x => x.Value == i).Key}");
                }

                Console.WriteLine($"0x{i:X4}: 0x{machineCode[i]:X2}  ; {consoleLog[i]}");
            }
        }

        private void AddBootLoader()
        {
            // Jump to main label
            int mainAddress = labels["main"];
            var bytes = BitConverter.GetBytes(mainAddress);

            machineCode[0] = 0xC3;      // JMP
            machineCode[1] = bytes[1];  // high byte
            machineCode[2] = bytes[0];  // low byte
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

            this.microcodeCompiler = Mcc.Compiler.Compile(microcodeSourceFile);

            Console.WriteLine("Microcode loaded!");
            Console.WriteLine();
        }
    }
}
