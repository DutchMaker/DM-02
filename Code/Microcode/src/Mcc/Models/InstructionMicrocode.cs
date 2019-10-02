using System.Collections.Generic;

namespace Mcc.Models
{
    public class InstructionMicrocode
    {
        private const string ADDRESS_FORMAT = "instruction|tstate|flags";

        public Instruction Instruction { get; set; }

        public FlagsState Flags { get; set; }

        public List<MicroInstruction> TStates { get; set; }
    }
}