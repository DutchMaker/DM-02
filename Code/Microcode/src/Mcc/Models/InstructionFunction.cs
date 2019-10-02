namespace Mcc.Models
{
    public class InstructionFunction : BitPattern
    {
        public InstructionFunction()
        {    
        }

        public InstructionFunction(string parseString)
        {
            this.ParseString(parseString);
        }
    }
}