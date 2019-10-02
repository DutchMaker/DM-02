namespace Mcc.Models
{
    public class AluFunction : BitPattern
    {
        public AluFunction()
        {            
        }
        
        public AluFunction(string parseString)
        {
            this.ParseString(parseString);
        }
    }
}