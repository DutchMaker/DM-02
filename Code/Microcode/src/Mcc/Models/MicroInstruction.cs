using System;
using System.Collections.Generic;
using System.Linq;

namespace Mcc.Models
{
    public class MicroInstruction
    {
        private const string INSTRUCTION_FORMAT_DATA = "1|operand_out|operand_load|0|0|function|0";           // '|' will be removed
        private const string INSTRUCTION_FORMAT_DATA_ALU = "1|operand_out|operand_load|1|alu_function|0";   
        private const string INSTRUCTION_FORMAT_FUNCTION = "0|function0|000000|function1|0";

        public MicroInstructionType Type { get; set; }

        public BitPattern OperandLoad { get; set; }

        public BitPattern OperandOut { get; set; }

        public List<BitPattern> ControlLines { get; set; }

        public AluFunction AluFunction { get; set; }

        public string GetControlBits()
        {
            string format = INSTRUCTION_FORMAT_FUNCTION;
            string result = format;

            if (this.Type == MicroInstructionType.DataOperation)
            {
                format = this.AluFunction == null
                    ? INSTRUCTION_FORMAT_DATA
                    : INSTRUCTION_FORMAT_DATA_ALU;
                
                result = format
                    .Replace("operand_out", this.OperandOut.Bits)
                    .Replace("operand_load", this.OperandLoad.Bits);
                
                if (this.AluFunction == null)
                {
                    if (this.ControlLines?.Count > 0)
                    {
                        result = result.Replace("function", this.ControlLines.First().Bits);
                    }
                    else
                    {
                        result = result.Replace("function", "0000");
                    }
                }
                else
                {
                    result = result.Replace("alu_function", this.AluFunction.Bits);
                }
            }
            else
            {
                for (int i = 0; i < 2; i++)
                {
                    result = result.Replace($"function{i}", 
                        (this.ControlLines.Count - 1 >= i) 
                            ? this.ControlLines[i].Bits
                            : "0000");
                }
            }

            return result;
        }

        public UInt16 GetControlWord()
        {
            return Converter.BitsToUInt(this.GetControlBits().Replace("|", string.Empty));
        }
    }
}