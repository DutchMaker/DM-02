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
            return null;
            //return $"{this.Negative}{this.Zero}{this.Overflow}{this.Carry}"
            //    .Replace("True", "1")
            //    .Replace("False", "0");
        }
    }
}