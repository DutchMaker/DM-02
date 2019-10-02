using System;

namespace Mcc.Models
{
    public class FlagsState
    {
        public bool? Carry { get; set; }

        public bool? Overflow { get; set; }

        public bool? Zero { get; set; }

        public bool? Negative { get; set; }

        public FlagsState()
        {            
        }

        public FlagsState(string flagString)
        {
            if (flagString.Equals("[C=1]", StringComparison.OrdinalIgnoreCase))
            {
                this.Carry = true;
            }

            if (flagString.Equals("[C=0]", StringComparison.OrdinalIgnoreCase))
            {
                this.Carry = false;
            }

            if (flagString.Equals("[O=1]", StringComparison.OrdinalIgnoreCase))
            {
                this.Overflow = true;
            }

            if (flagString.Equals("[O=0]", StringComparison.OrdinalIgnoreCase))
            {
                this.Overflow = false;
            }

            if (flagString.Equals("[Z=1]", StringComparison.OrdinalIgnoreCase))
            {
                this.Zero = true;
            }

            if (flagString.Equals("[Z=0]", StringComparison.OrdinalIgnoreCase))
            {
                this.Zero = false;
            }

            if (flagString.Equals("[N=1]", StringComparison.OrdinalIgnoreCase))
            {
                this.Negative = true;
            }

            if (flagString.Equals("[N=0]", StringComparison.OrdinalIgnoreCase))
            {
                this.Negative = false;
            }
        }

        public string ToBits()
        {
            return $"{(this.Negative == null ? "x" : this.Negative.ToString())}{(this.Zero == null ? "x" : this.Zero.ToString())}{(this.Overflow == null ? "x" : this.Overflow.ToString())}{(this.Carry == null ? "x" : this.Carry.ToString())}"
                .Replace("True", "1")
                .Replace("False", "0");
        }

        public bool Match(int flags)
        {
            string bits = this.ToBits();
            string compareBits = Convert.ToString(flags, 2).PadLeft(4, '0');

            for (int i = 0; i < 4; i++)
            {
                if (bits[i] == 'x')
                {
                    continue;
                }

                if (bits[i] != compareBits[i])
                {
                    return false;
                }
            }

            return true;
        }
    }
}