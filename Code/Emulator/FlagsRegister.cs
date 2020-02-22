namespace Emulator
{
    public class FlagsRegister
    {
        public Bus BUS { get; set; }

        public bool Carry { get; set; }

        public bool Overflow { get; set; }

        public bool Zero { get; set; }

        public bool Negative { get; set; }
    }
}