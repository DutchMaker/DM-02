using System;

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
    }
}