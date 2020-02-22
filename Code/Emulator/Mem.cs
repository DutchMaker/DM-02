namespace Emulator
{
    public class Mem
    {
        public Bus BUS { get; set; }

        public byte Value { get; set; }

        public bool _Out { get; set; }

        public bool _Load { get; set; }
    }
}