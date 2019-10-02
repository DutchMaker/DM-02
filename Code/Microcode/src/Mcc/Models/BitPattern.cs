using System;

namespace Mcc.Models
{
    public class BitPattern
    {
        public string Identifier { get; set; }

        public string Bits { get; set; }

        public virtual void ParseString(string str)
        {
            string[] columns = str.Split(':', StringSplitOptions.RemoveEmptyEntries);

            if (columns.Length != 2)
            {
                throw new CompilerException($"Invalid definition (not enough columns): '{str}'");
            }

            this.Bits = columns[0];
            this.Identifier = columns[1];
        }
    }
}