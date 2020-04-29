using System;
using System.Linq;

namespace Mcc.Models
{
    public class Instruction : BitPattern
    {
        public string Mnemonic 
        { 
            get => this.Identifier;
            set => this.Identifier = value;
        }

        public byte Opcode { get; set; }

        public string OpcodeString { get; set; }

        public byte ByteCount { get; set; }

        public Instruction()
        {            
        }

        public Instruction(string parseString)
        {
            this.ParseString(parseString);
        }

        public override void ParseString(string str)
        {
            string[] columns = str.Split(':', StringSplitOptions.RemoveEmptyEntries);

            if (columns.Length != 3)
            {
                throw new CompilerException($"Invalid instruction definition: '{str}'");
            }

            try
            {
                this.OpcodeString = columns[0];
                this.ByteCount = Convert.ToByte(columns[1]);
                this.Mnemonic = columns[2];

                this.Opcode = Converter.HexToByte(this.OpcodeString);
                this.Bits = Convert.ToString(this.Opcode, 2).PadLeft(8, '0');
            }
            catch (Exception ex)
            {
                throw new CompilerException($"Exception occurred while parsing instruction definition '{str}': {ex.Message}");
            }
        }

        /// <summary>
        /// Indicates whether the given line of assembly code matches this instruction.
        /// </summary>
        /// <param name="line"></param>
        /// <param name="data">If the line of code contains data (value or address), it's output here.</param>
        /// <returns></returns>
        public bool Match(string line, out string data)
        {
            if (ByteCount == 1 && line.Equals(Mnemonic))
            {
                data = null;
                return true;
            }

            if (line.Contains("#"))
            {
                string mnemonic = line.Split(',').First();
                data = line.Split(',').Last().Replace("#", string.Empty);

                if (Mnemonic.Equals(mnemonic + ",value"))
                {
                    return true;
                }
            }

            if (Mnemonic.Contains("address"))
            {
                if (line.Contains("(") && !Mnemonic.Contains("("))
                {
                    data = null;
                    return false;
                }
                
                string[] beforeAfter = Mnemonic.Split("address");

                if (line.StartsWith(beforeAfter[0]) && (string.IsNullOrEmpty(beforeAfter[1]) || line.EndsWith(beforeAfter[1])))
                {
                    data = line.Replace(beforeAfter[0], "");
                    
                    if (!string.IsNullOrEmpty(beforeAfter[1]))
                    {
                        data = data.Replace(beforeAfter[1], "");
                    }

                    return true;
                }
            }

            data = null;
            return false;
        }
    }
}