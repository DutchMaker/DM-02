namespace Mcc.Models
{
    public class Operand : BitPattern
    {
        public Operand()
        {
        }

        public Operand(string parseString)
        {
            this.ParseString(parseString);
        }
    }
}