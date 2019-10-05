using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using Mcc.Models;

namespace Mcc
{
    public class Compiler
    {
        private const string SECTION_OPERANDS = ".operands";
        private const string SECTION_FUNCTIONS = ".functions";
        private const string SECTION_INSTRUCTIONS = ".instructions";
        private const string SECTION_ALUFUNCTIONS = ".alu";
        private const string SECTION_CODE = ".code";
        private readonly string[] REGISTERS = { "A", "B", "C", "H", "L" };
        private readonly string[] REGISTERS_PAIRS = { "BC", "HL" };
                
        private static Compiler _compiler;

        private string source;
        
        public List<Instruction> Instructions = new List<Instruction>();
        public List<Operand> Operands = new List<Operand>();
        public List<InstructionFunction> InstructionFunctions = new List<InstructionFunction>();
        public List<AluFunction> AluFunctions = new List<AluFunction>();
        public List<InstructionMicrocode> MicrocodeSource = new List<InstructionMicrocode>();

        private Dictionary<int, UInt16> microcode = new Dictionary<int, ushort>();

        public static void Compile(string sourceFileName)
        {
            string romFileName = sourceFileName.Split('.', StringSplitOptions.RemoveEmptyEntries).First() + ".rom";
            string logisimImageFileName = sourceFileName.Split('.', StringSplitOptions.RemoveEmptyEntries).First() + ".img";
            string source = File.ReadAllText(sourceFileName);

            _compiler = new Compiler(source);
            _compiler.Compile();
            _compiler.Save(romFileName, logisimImageFileName);
        }

        public Compiler(string source)
        {
            this.source = source;
        }

        public void Initialize()
        {
            this.CleanupSource();
            this.LoadBitPatterns();
        }

        /// <summary>
        /// Compiles the microcode and store the result in memory.
        /// </summary>
        public void Compile()
        {
            this.Initialize();
            this.LoadCode();
            this.CompileCode();
        }

        /// <summary>
        /// Saves the compiled microcode to disk.
        /// </summary>
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

            using (var writer = new BinaryWriter(File.Open(romFileName, FileMode.CreateNew)))
            {
                // ROM image for EPROM needs to be little-endian format.
                // (low byte first, high byte second)
                foreach (int address in this.microcode.Keys)
                {
                    byte high = (byte)(this.microcode[address] >> 8);
                    byte low = (byte)(this.microcode[address] & 0xff);

                    // The offset is calculated in bytes, our values are 2 bytes each.
                    // Therefore we need to store at address*2.
                    writer.Seek(address*2, SeekOrigin.Begin);
                    writer.Write(low);
                    writer.Write(high);
                }
            }

            using (TextWriter writer = new StreamWriter(File.Open(logisimImageFileName, FileMode.CreateNew)))
            {
                // The Logisim image is written in a plain text format.
                // It has 8 16-bit values per row, separated by space.
                // Values are formatted big-endian.
                writer.WriteLine("v2.0 raw\n");
                int address = 0;

                for (int row = 0; row < UInt16.MaxValue / 8; row++)
                {
                    string rowData = string.Empty;

                    for (int col = 0; col < 8; col++)
                    {
                        if (this.microcode.ContainsKey(address))
                        {
                            rowData += $"{Converter.UIntToHex(this.microcode[address])} ";
                        }
                        else
                        {
                            rowData += "0000 ";
                        }

                        address++;
                    }

                    writer.WriteLine(rowData.Trim());
                }
            }

            Console.WriteLine($"Done ({sw.ElapsedMilliseconds} ms)");
        }

        private void CleanupSource()
        {
            // Replace Windows-style newlines with Linux-style newlines to avoid parsing issues.
            source = source.Replace("\r\n", "\n");

            // Remove indentations.
            source = source.Replace("\t", string.Empty);
            while (source.Contains("  "))
            {
                source = source.Replace("  ", " ");
            }

            // Remove whitespace lines.
            while (source.Contains("\n\n"))
            {
                source = source.Replace("\n\n", "\n");
            }

            source = source.Replace("\n \n", "\n");
            source = source.Replace("\n ", "\n");
            source = source.Replace(" \n", "\n");

            // Remove comments.
            while (source.Contains("#"))
            {
                int commentStart = source.IndexOf("#");
                int commentEnd = source.IndexOf("\n", commentStart);

                if (commentEnd == -1)
                {
                    commentEnd = source.Length - commentStart;
                }

                string beforeComment = source.Substring(0, commentStart);
                string afterComment = source.Substring(commentEnd + 1);

                source = beforeComment + afterComment;
            }
        }

        private void LoadBitPatterns()
        {
            this.Operands = this.LoadBitPattern<Operand>(SECTION_OPERANDS);
            this.InstructionFunctions = this.LoadBitPattern<InstructionFunction>(SECTION_FUNCTIONS);
            this.AluFunctions = this.LoadBitPattern<AluFunction>(SECTION_ALUFUNCTIONS);
            this.Instructions = this.LoadBitPattern<Instruction>(SECTION_INSTRUCTIONS);
        }

        private List<T> LoadBitPattern<T>(string section)
            where T: BitPattern, new()
        {
            string sectionCode = this.ExtractSection(section);

            var patterns = sectionCode.Split('\n', StringSplitOptions.RemoveEmptyEntries)
                .Select(s => 
                {
                    var t = new T();
                    t.ParseString(s);

                    return t;
                })
                .ToList();

            // Check for unique opcodes.
            patterns.ForEach(i => 
            {
                if (patterns.Count(c => c.Bits == i.Bits) > 1)
                {
                    throw new CompilerException($"Bit pattern '{i.Bits}' (hex: {Convert.ToByte(i.Bits, 2):X2}) is assigned to more than one instruction.");
                }
            });

            // Check for unique identifiers.
            patterns.ForEach(i => 
            {
                if (patterns.Count(c => c.Identifier == i.Identifier) > 1)
                {
                    throw new CompilerException($"Identifier (mnemonic) '{i.Identifier}' is defined to more than once.");
                }
            });

            return patterns;
        }

        private void LoadCode()
        {
            var sw = Stopwatch.StartNew();
            Console.Write("Loading code...");

            int cursor = this.source.IndexOf(SECTION_CODE, StringComparison.OrdinalIgnoreCase);

            if (cursor == -1)
            {
                throw new CompilerException($"Could not find '{SECTION_CODE}' section");
            }

            // Instruction starts on next line.
            cursor = this.source.IndexOf("\n", cursor) + 1;

            // Move cursor through the source file until we reach the end.
            while (cursor > -1 && cursor < this.source.Length - 1)
            {
                // Get instruction mnemonic.
                int mnemonicEnd = this.source.IndexOf("\n", cursor);
                string mnemonic = this.source.Substring(cursor, mnemonicEnd - cursor);

                if (mnemonic.Equals(".end", StringComparison.OrdinalIgnoreCase))
                {
                    // End of .code block reached.
                    break;
                }

                // Get t-states code.
                cursor = mnemonicEnd + 1;
                int tstatesEnd = this.source.IndexOf(".end", cursor, StringComparison.OrdinalIgnoreCase);
                string tstates = string.Empty;

                if (tstatesEnd - cursor > 0)
                {
                    tstates = this.source.Substring(cursor, tstatesEnd - cursor - 1);
                }
                
                FlagsState flags = null;

                // Get flags criteria.
                if (mnemonic.IndexOf("[") > -1)
                {
                    int flagStart = mnemonic.IndexOf("[");
                    int flagEnd = mnemonic.IndexOf("]", flagStart);
                    string flagString = mnemonic.Substring(flagStart, flagEnd - flagStart + 1);

                    mnemonic = mnemonic.Replace(flagString, string.Empty)
                        .Replace("  ", " ")
                        .Trim();

                    flags = new FlagsState(flagString);
                }

                // If we don't need to replace anything in the source code, just add the instruction to memory.
                if (mnemonic.IndexOf("r1", StringComparison.OrdinalIgnoreCase) > -1 || mnemonic.IndexOf("r2", StringComparison.OrdinalIgnoreCase) > -1
                    || mnemonic.IndexOf("hl1", StringComparison.OrdinalIgnoreCase) > -1 || mnemonic.IndexOf("hl2", StringComparison.OrdinalIgnoreCase) > -1)
                {
                    foreach (string r1 in REGISTERS)
                    {
                        foreach (string r2 in REGISTERS)
                        {
                            foreach (string hl1 in REGISTERS_PAIRS)
                            {
                                foreach (string hl2 in REGISTERS_PAIRS)
                                {
                                    string targetMnemonic = mnemonic.Replace("r1", r1).Replace("r2", r2)
                                        .Replace("hl1", hl1).Replace("hl2", hl2);

                                    if (this.Instructions.Exists(i => i.Mnemonic.Equals(targetMnemonic, StringComparison.OrdinalIgnoreCase))
                                        && !this.MicrocodeSource.Exists(c => c.Instruction.Mnemonic.Equals(targetMnemonic, StringComparison.OrdinalIgnoreCase)))
                                    {
                                        string targetTstates = tstates.Replace("r1", r1).Replace("r2", r2)
                                            .Replace("hl1", hl1).Replace("hl2", hl2)
                                            .Replace("h1", $"{hl1[0]}").Replace("l1", $"{hl1[1]}")
                                            .Replace("h2", $"{hl2[0]}").Replace("l2", $"{hl2[1]}");

                                        this.AddToMicrocodeSource(targetMnemonic, flags, targetTstates);
                                    }
                                }
                            }
                        }
                    }
                }
                else
                {
                    this.AddToMicrocodeSource(mnemonic, flags, tstates);
                }

                // Move cursor to next instruction.
                cursor = this.source.IndexOf("\n", tstatesEnd) + 1;
            }

            Console.WriteLine($"Done ({sw.ElapsedMilliseconds} ms)");
        }

        private void CompileCode()
        {
            var sw = Stopwatch.StartNew();
            Console.Write("Compiling code...");

            foreach (var c in this.MicrocodeSource)
            {
                for (int t = 0; t < c.TStates.Count; t++)
                {
                    for (int f = 0; f < 16; f++)
                    {
                        if (c.Flags != null && !c.Flags.Match(f))
                        {
                            continue;
                        }

                        string instructionBits = c.Instruction.Bits;
                        string tstateBits = Convert.ToString(t, 2).PadLeft(4, '0');
                        string flagsBits = Convert.ToString(f, 2).PadLeft(4, '0');
                        string addressBits = instructionBits + tstateBits + flagsBits;

                        int address = Convert.ToInt32(addressBits, 2);
                        this.microcode.Add(address, c.TStates[t].GetControlWord());
                    }
                }
            }

            Console.WriteLine($"Done ({sw.ElapsedMilliseconds} ms)");
        }

        private void AddToMicrocodeSource(string mnemonic, FlagsState flags, string tstates)
        {
            var instructionCode = new InstructionMicrocode
            {
                Instruction = this.Instructions.FirstOrDefault(i => i.Mnemonic.Equals(mnemonic, StringComparison.OrdinalIgnoreCase)),
                Flags = flags,
                TStates = this.ParseTStateCode(tstates)
            };

            if (instructionCode.Instruction == null)
            {
                throw new CompilerException($"Could not find instruction definition for '{mnemonic}'");
            }

            this.MicrocodeSource.Add(instructionCode);
        }

        private List<MicroInstruction> ParseTStateCode(string tstates)
        {
            var result = new List<MicroInstruction>();

            if (string.IsNullOrEmpty(tstates))
            {
                return result;
            }

            tstates = tstates.Replace(" ", string.Empty);
            int cursor = tstates.IndexOf(":");

            while (cursor > -1)
            {
                int tstateEnd = tstates.IndexOf(":", cursor + 1);

                if (tstateEnd == -1)
                {
                    tstateEnd = tstates.Length;
                }

                string tstate = tstates.Substring(cursor + 1, tstateEnd - cursor - 1);
                string[] uinstructions = tstate.Split('\n', StringSplitOptions.RemoveEmptyEntries);

                var microInstruction = new MicroInstruction
                {
                    Type = MicroInstructionType.FunctionOperation,
                    ControlLines = new List<BitPattern>()
                };
                
                for (int i = 0; i < uinstructions.Length; i++)
                {
                    if (i == 0 && uinstructions[i].IndexOf("[data]", StringComparison.OrdinalIgnoreCase) > -1)
                    {
                        microInstruction.Type = MicroInstructionType.DataOperation;

                        string aluFuncString = uinstructions[i].Replace("[data]", string.Empty)
                            .Replace("[", string.Empty)
                            .Replace("]", string.Empty);

                        if (!string.IsNullOrWhiteSpace(aluFuncString) && this.AluFunctions.Exists(f => f.Identifier.Equals(aluFuncString, StringComparison.OrdinalIgnoreCase)))
                        {
                            microInstruction.AluFunction = this.AluFunctions.FirstOrDefault(f => f.Identifier.Equals(aluFuncString, StringComparison.OrdinalIgnoreCase));
                        }
                    }
                    else if (i == 0 && uinstructions[i].IndexOf("[function]", StringComparison.OrdinalIgnoreCase) > -1)
                    {
                        // Ignore
                    }
                    else
                    {
                        var function = this.InstructionFunctions.FirstOrDefault(o => o.Identifier.Equals(uinstructions[i], StringComparison.OrdinalIgnoreCase));
                        var operand = this.Operands.FirstOrDefault(o => 
                            $"{o.Identifier}_load".Equals(uinstructions[i], StringComparison.OrdinalIgnoreCase)
                            || $"{o.Identifier}_out".Equals(uinstructions[i], StringComparison.OrdinalIgnoreCase));
                        
                        if (operand != null)
                        {
                            if (uinstructions[i].IndexOf("_load", StringComparison.OrdinalIgnoreCase) > -1)
                            {
                                microInstruction.OperandLoad = operand;
                            }
                            else if (uinstructions[i].IndexOf("_out", StringComparison.OrdinalIgnoreCase) > -1)
                            {
                                microInstruction.OperandOut = operand;
                            }
                        }
                        else if (function != null)
                        {
                            microInstruction.ControlLines.Add(function);
                        }
                        else if (int.TryParse(uinstructions[i], out int tmp))
                        {
                            // Ignore
                        }
                        else
                        {
                            throw new CompilerException($"Could not locate operand or function '{uinstructions[i]}' for tstate at position {cursor}");
                        }
                    }
                }

                result.Add(microInstruction);

                cursor = tstateEnd < tstates.Length 
                    ? tstates.IndexOf(":", tstateEnd)
                    : -1;
            }

            return result;
        }
        
        private string ExtractSection(string sectionName)
        {
            int sectionStart = source.IndexOf(sectionName, StringComparison.OrdinalIgnoreCase);

            if (sectionStart == -1)
            {
                throw new CompilerException($"Could not find '{sectionName}' section");
            }

            // Extract all the code for this section.
            int contentStart = source.IndexOf("\n", sectionStart);
            int contentEnd = source.IndexOf(".end", contentStart, StringComparison.OrdinalIgnoreCase);

            string sectionCode = source.Substring(contentStart + 1, contentEnd - contentStart - 2);

            return sectionCode;
        }
    }
}
